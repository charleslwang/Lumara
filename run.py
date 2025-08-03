import os
from app import create_app, db
from app.models.user import User
from app.models.refinement import Refinement

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Refinement': Refinement}

if __name__ == '__main__':
    app.run(debug=True, port=5001)
