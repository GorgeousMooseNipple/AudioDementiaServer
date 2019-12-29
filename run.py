from ad_server import create_app, db


app = create_app()


@app.shell_context_processor
def get_shell_context():
    return {'db': db, 'app': app}
