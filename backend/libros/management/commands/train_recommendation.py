"""
Commands for training recommendation models
"""
from django.core.management.base import BaseCommand
from core.services.recommendation_service import RecomendationEngine


class Command(BaseCommand):
    """
    Command to train the recommendation model.

    Args:
        BaseCommand (BaseCommand): Command base class from Django.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force the retraining even though an existing model is present',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting recommendation model training...')

        try:
            engine = RecomendationEngine()
            engine.train()

            self.stdout.write(
                self.style.SUCCESS('Model trained successfully')
            )
            self.stdout.write(
                f'Users in the model: {len(engine.user_ids)}'
            )
        except ValueError as e:
            self.stdout.write(
                self.style.WARNING(f'The model was not trained: {e}')
            )
            self.stdout.write(
                'Be sure that there is enough data in InteresUsuario, \
                    Favorito and Recomendacion models'
            )
            raise
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'An error occurred during training: {e}')
            )
            raise
