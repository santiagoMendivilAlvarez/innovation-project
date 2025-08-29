export default function TestBootstrap() {
  return (
    <div className="container mt-5">
      <div className="row">
        <div className="col-md-6 mx-auto">
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">¡Bootstrap funcionando!</h3>
            </div>
            <div className="card-body">
              <p className="card-text">
                YA QUEDO EL Bootstrap
              </p>
              <button className="btn btn-primary me-2">Botoncito 1 </button>
              <button className="btn btn-outline-secondary">Botoncito 2</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}