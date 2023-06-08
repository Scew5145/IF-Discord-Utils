import json

# google api includes
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools


class GoogleFormAPI:
    SCOPES = "https://www.googleapis.com/auth/forms.body"
    DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

    store = file.Storage("token.json")
    creds = None
    forms_service = None

    def __init__(self):
        if not self.creds or self.creds.invalid:
            flow = client.flow_from_clientsecrets('F:/InfiniteFusion/GoogleAPIs/client_secret_813113044012-sbu2g7a10gsg6c9d3d80ghfdqejt8866.apps.googleusercontent.com.json', self.SCOPES)
            self.creds = tools.run_flow(flow, self.store)

        self.form_service = discovery.build('forms', 'v1', http=self.creds.authorize(
            Http()), discoveryServiceUrl=self.DISCOVERY_DOC, static_discovery=False)

    def create_google_form(self, collisions_file, limit=50):
        # Request body for creating a form
        new_form = {
            "info": {
                "title": "Quickstart form",
            }
        }

        # Request body to add a multiple-choice question
        new_question = {
            "requests": [{
                "createItem": {
                    "item": {
                        "title": "In what year did the United States land a mission on the moon?",
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [
                                        {"value": "1965"},
                                        {"value": "1967"},
                                        {"value": "1969"},
                                        {"value": "1971"}
                                    ],
                                    "shuffle": True
                                }
                            }
                        },
                    },
                    "location": {
                        "index": 0
                    }
                }
            }]
        }

        # Creates the initial form
        result = self.form_service.forms().create(body=new_form).execute()

        # Adds the question to the form
        question_setting = self.form_service.forms().batchUpdate(formId=result["formId"], body=new_question).execute()

        # Prints the result to show the question has been added
        get_result = self.form_service.forms().get(formId=result["formId"]).execute()
        print(get_result)
        return


if __name__ == '__main__':
    form = GoogleFormAPI()
    form.create_google_form("poopy")
