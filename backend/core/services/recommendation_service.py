"""
Recommendation service
"""
# pylint: disable=E1101
from pathlib                  import Path
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing    import MinMaxScaler
from django.core.cache        import cache
from django.db.models         import Count, QuerySet
from libros.models            import Libro
from profiles.models          import InteresUsuario, Favorito, Recomendacion


class RecomendationEngine:
    """
    Recommendation
    """
    def __init__(self):
        self.user_similarity_matrix = None
        self.user_ids = None
        self.model_path = Path('ml_models/recommendation_model.pkl')


    def prepare_user_features(self: 'RecomendationEngine') -> pd.DataFrame:
        """
        Get and prepare the user features to train the model based in this cols.

        Returns:
            pd.DataFrame: The dataframe with the user features.
        """
        intereses    = InteresUsuario.objects.select_related('usuario', 'categoria').all()
        df_intereses = pd.DataFrame(
            list(intereses.values('usuario_id', 'categoria_id', 'nivel_interes')))
        favoritos = Favorito.objects.select_related('libro__categoria').values(
            'usuario_id', 'libro__categoria_id'
        ).annotate(count=Count('id'))
        df_favoritos = pd.DataFrame(list(favoritos))

        if not df_favoritos.empty:
            df_favoritos.columns = ['usuario_id', 'categoria_id', 'peso']
            df_favoritos['peso'] = df_favoritos['peso'] * 5

        if df_intereses.empty and df_favoritos.empty:
            return None

        if df_intereses.empty:
            df_combined = df_favoritos
            feature_col = 'peso'
        elif df_favoritos.empty:
            df_combined = df_intereses
            feature_col = 'nivel_interes'
        else:
            df_intereses.rename(columns={'nivel_interes': 'valor'}, inplace=True)
            df_favoritos.rename(columns={'peso': 'valor'}, inplace=True)
            df_combined = pd.concat([df_intereses, df_favoritos])
            feature_col = 'valor'

        user_features = df_combined.pivot_table(
            index      = 'usuario_id',
            columns    = 'categoria_id',
            values     = feature_col,
            aggfunc    = 'sum',
            fill_value = 0
        )
        return user_features


    def prepare_collaborative_features(self: 'RecomendationEngine') -> pd.DataFrame:
        """
        Prepare the collaborative features for the categories and recomendations

        Returns:
            pd.DataFrame: The dataframe with the collaborative features.
        """
        recomendaciones = Recomendacion.objects.select_related(
            'libro').values('usuario_id', 'libro__categoria_id', 'calificacion_recomendacion')
        df = pd.DataFrame(list(recomendaciones))
        if df.empty:
            return None
        collab_features = df.pivot_table(
            index = 'usuario_id',
            columns="libro__categoria_id",
            values="calificacion_recomendacion",
            aggfunc='mean',
            fill_value=0
        )
        return collab_features


    def train(self: 'RecomendationEngine') -> 'RecomendationEngine':
        """
        Method to train the model with the features previously loaded.

        Args:
            self (RecomendationEngine): The recommendation engine object. 

        Returns:
            RecomendationEngine: The trained recommendation engine object.
        """
        user_features = self.prepare_user_features()
        collab_features = self.prepare_collaborative_features()
        if user_features is not None and collab_features is not None:
            all_cols = sorted(set(user_features.columns) | set(collab_features.columns))
            user_features = user_features.reindex(columns=all_cols, fill_value=0)
            collab_features = collab_features.reindex(columns=all_cols, fill_value=0)
            all_users = sorted(set(user_features.index) | set(collab_features.index))
            user_features = user_features.reindex(index=all_users, fill_value=0)
            collab_features = collab_features.reindex(index=all_users, fill_value=0)
            combined = user_features * 0.7 + collab_features * 0.3
        elif user_features is not None:
            combined = user_features
        else:
            combined = collab_features

        scaler = MinMaxScaler()
        normalized = scaler.fit_transform(combined)

        self.user_similarity_matrix = cosine_similarity(normalized)
        self.user_ids = combined.index.tolist()
        self._save_model()
        return self


    def _save_model(self: 'RecomendationEngine') -> None:
        """
        Method to save the model into a file.

        Args:
            self (RecomendationEngine): The recommendation engine object.
        """
        self.model_path.mkdir(exist_ok=True, parents=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'similarity_matrix': self.user_similarity_matrix,
                'user_ids': self.user_ids
            }, f)


    def _load_model(self: 'RecomendationEngine') -> bool:
        """
        Method to load the existing model.

        Args:
            self (RecomendationEngine): The recomendation engine object.

        Returns:
            bool: True if exists and was loaded. False otherwise
        """
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.user_similarity_matrix = data['similarity_matrix']
                self.user_ids = data['user_ids']
            return True
        return False


    def get_recommendations(self: 'RecomendationEngine', user_id: int, top_n: int = 10) -> QuerySet:
        """
        Method to get the recommendations for a specific user.

        Args:
            self (RecomendationEngine): The recomendation engine object.
            user_id (int): The user ID that is currently active.
            top_n (int, optional): The number of recommendations to return. Defaults to 10.

        Returns:
            QuerySet: A queryset containing the recommended books.
        """
        cache_key = f'recommendations_user_{user_id}_top_{top_n}'
        cached    = cache.get(cache_key)
        if cached:
            return Libro.objects.filter(id__in=cached)

        if self.user_similarity_matrix is None:
            if not self._load_model(): # Initial
                return self._cold_start_recommendations(user_id, top_n)

        if user_id not in self.user_ids: # If not exists the user
            return self._cold_start_recommendations(user_id, top_n)

        user_idx = self.user_ids.index(user_id)
        similarities = self.user_similarity_matrix[user_idx]
        similar_users_idx = np.argsort(similarities)[::-1][1:11]
        similar_user_ids = [self.user_ids[idx] for idx in similar_users_idx]

        recommended_books = Favorito.objects.filter(
            usuario_id__in=similar_user_ids
        ).values('libro_id').annotate(
            score=Count('libro_id')
        ).order_by('-score')

        user_favorites = Favorito.objects.filter(
            usuario_id=user_id
        ).values_list('libro_id', flat=True)
        recommended_books = recommended_books.exclude(
            libro_id__in=user_favorites
        )
        recommended_books = self._boost_by_interests(user_id, recommended_books)

        libro_ids = [item['libro_id'] for item in recommended_books[:top_n]]
        cache.set(cache_key, libro_ids, timeout=3600)
        return Libro.objects.filter(id__in=libro_ids)


    def _cold_start_recommendations(self: 'RecomendationEngine',
                                    user_id: int, top_n: int) -> QuerySet:
        """
        Cold start recommendations based on user interests or popular books.

        Args:
            self (RecomendationEngine): The recomendation engine object.
            user_id (int): The user ID that is currently active.
            top_n (int): The number of recommendations to return.

        Returns:
            QuerySet: A queryset containing the recommended books.
        """
        interests = InteresUsuario.objects.filter(
            usuario_id=user_id
        ).order_by('-nivel_interes').values_list('categoria_id', flat=True)[:3]

        if interests:
            libros = Libro.objects.filter(
                categoria_id__in=interests,
                disponible=True
            ).exclude(
                favoritos__usuario_id=user_id
            ).order_by('-calification')[:top_n]
            if libros.exists():
                return libros
        populares = Libro.objects.filter(
            disponible=True
        ).annotate(
            num_favoritos=Count('favoritos')
        ).order_by('-num_favoritos', '-calificacion')[:top_n]
        return populares


    def get_similar_books(self: 'RecomendationEngine', libro_id: int, top_n: int = 6):
        """
        Method to get books that are related to others.

        Args:
            self (RecomendationEngine): The recommendation engine object.
            libro_id (int): The id for the book searched.
            top_n (int, optional): The number of similar books to return. Defaults to 6.

        Returns:
            QuerySet: A queryset containing the similar books.
        """
        try:
            libro = Libro.objects.get(id=libro_id)
        except Libro.DoesNotExist:
            return Libro.objects.none()
        similares = Libro.objects.filter(
            categoria=libro.categoria,
            disponible=True
        ).exclude(
            id=libro_id
        ).annotate(
            num_favoritos=Count('favoritos')
        ).order_by('-calificacion', '-num_favoritos')[:top_n]
        return similares
