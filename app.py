from flask import Flask, request, render_template, redirect, make_response, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.wrappers import response
from surveys import surveys 

CURRENT_SURVEY_KEY = 'current_survey'
RESPONSES_KEY = 'responses'


app = Flask(__name__)
app.config['SECRET_KEY'] = "1234"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)



@app.route("/")
def show_pick_survey_form():
    """Page to pick survey"""
    return render_template("select_survey.html", surveys = surveys)

@app.route("/", methods = ['POST'])
def select_survey():
    """select a survey"""
    survey_id = request.form['survey_code']

    #don't let them re-take survey until cookie times out
    if request.cookies.get(f"completed_{survey_id}"):
        return render_template("already-done.html")
    
    survey = surveys[survey_id]
    session[CURRENT_SURVEY_KEY] = survey_id

    return render_template("survey_start.html", survey=survey)
    
@app.route("/begin", methods = ["POST"])
def start_survey():
    """Clear the session of responses"""

    session[RESPONSES_KEY] = []

    return redirect("/questions/0")

@app.route("/answer", methods=["POST"])
def handle_question():
    """Save response and redirect to next question"""

    choice = request.form['answer']
    text = request.form.get('text', "")

    #add this response to the list in the session
    responses = session[RESPONSES_KEY]
    responses.append({"choice": choice, "text": text})

    #add this response to the session
    session[RESPONSES_KEY] = responses
    survey_code = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_code]

    if (len(responses) == len(survey.questions)):
      # All questions answered go to complete page
        return redirect("/complete")

    else:
        return redirect(f"/questions/{len(responses)}")

@app.route("/questions/<int:id>")
def show_question(id):
    """Page displaying survey question"""
    
    responses = session.get(RESPONSES_KEY)
    survey_code = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_code]

    if (responses is None):
        # trying to access question page too soon
        return redirect("/")

    if (len(responses) == len(survey.questions)):
        # All questions answered go to complete page
        return redirect("/complete")

    if (len(responses) != id):
        # Try to access question out of order.
        flash(f"Invalid question id: {id}.")
        return redirect(f"/questions/{len(responses)}")
    
    question = survey.questions[id]

    return render_template("question.html", question_num = id, question = question)


@app.route("/complete")
def complete():
    """Survey finished, show complete page"""

    survey_id = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_id]
    responses = session[RESPONSES_KEY]

    html = render_template("complete.html", survey=survey, responses=responses)

    # Set cookie noting this survey is done so they can't re-do it
    response = make_response(html)
    response.set_cookie(f"completed_{survey_id}", "yes", max_age=60)
    return response
