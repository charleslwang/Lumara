import os
from flask import Blueprint, render_template, redirect, url_for, flash, session, current_app, request
from flask_login import current_user, login_required
from app.forms import RefinementForm
from app.utils.refinery_wrapper import RefineryWrapper

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html', title='Home')

@bp.route('/refine', methods=['GET', 'POST'])
@login_required
def refine():
    form = RefinementForm()
    if form.validate_on_submit():
        if not current_user.gemini_api_key:
            flash('Please set your Gemini API key in settings before refining.', 'warning')
            return redirect(url_for('auth.settings'))

        session['prompt'] = form.prompt.data
        session['iterations'] = form.iterations.data
        
        return redirect(url_for('main.run_refinement'))

    return render_template('refine.html', title='Refine Prompt', form=form)

@bp.route('/refine/run')
@login_required
def run_refinement():
    prompt = session.get('prompt')
    iterations = session.get('iterations')

    if not prompt or not iterations:
        flash('No prompt found to refine. Please start again.', 'warning')
        return redirect(url_for('main.refine'))

    api_key = current_user.gemini_api_key
    refinery_path = current_app.config['REFINERY_PROJECT_PATH']

    # This is a placeholder for streaming results.
    # A real implementation would use WebSockets or Server-Sent Events.
    return render_template('results.html', title='Refinement Results', prompt=prompt, iterations=iterations)


@bp.route('/stream_refinement')
@login_required
def stream_refinement():
    from flask import Response
    import time
    import json

    prompt = session.get('prompt')
    iterations = session.get('iterations')

    if not prompt or not iterations:
        def error_stream():
            error_data = json.dumps({'error': 'Session data not found.'})
            yield f"data: {error_data}\n\n"
        return Response(error_stream(), mimetype='text/event-stream')

    api_key = current_user.gemini_api_key
    refinery_path = current_app.config['REFINERY_PROJECT_PATH']

    def generate():
        try:
            wrapper = RefineryWrapper(api_key=api_key, refinery_project_path=refinery_path)
            pipeline = wrapper._get_pipeline()

            for result_json in pipeline.run_iterative(prompt, iterations):
                # The result is already a JSON string from the pipeline
                yield f"data: {result_json}\n\n"
                time.sleep(0.1)  # Prevent overwhelming the browser

        except Exception as e:
            error_message = f"An error occurred while setting up or running the pipeline: {str(e)}"
            error_data = json.dumps({'error': error_message})
            yield f"data: {error_data}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    # db.session.rollback() # If you have a db session
    return render_template('500.html'), 500
