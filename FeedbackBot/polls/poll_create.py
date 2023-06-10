import json
from pathlib import Path

import poll_diff

# google api includes
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


# Meant to represent a single google form object, to be used in voting. Contains both a reference to the
# original folders that were compared, an output target folder, and a link to the vote itself
class GoogleForm:
    SCOPES = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/forms.body"]
    DISCOVERY_DOC_FORMS = "https://forms.googleapis.com/$discovery/rest?version=v1"
    DISCOVERY_DOC_DRIVE = "https://forms.googleapis.com/$discovery/rest?version=v1"

    store = file.Storage("token.json")
    creds = None
    forms_service = None
    collisions_json = None
    drive_service = None

    def __init__(self):
        if not self.creds or self.creds.invalid:
            flow = client.flow_from_clientsecrets(
                'F:/InfiniteFusion/GoogleAPIs/client_secret_813113044012-sbu2g7a10gsg6c9d3d80ghfdqejt8866.apps.googleusercontent.com.json',
                self.SCOPES)
            self.creds = tools.run_flow(flow, self.store)

        self.form_service = discovery.build('forms', 'v1', http=self.creds.authorize(
            Http()), discoveryServiceUrl=self.DISCOVERY_DOC_FORMS, static_discovery=False)
        self.drive_service = discovery.build('drive', 'v3', http=self.creds.authorize(
            Http()), static_discovery=False)

    def create_google_form(self, collisions_file_name, poll_old_alts=False, limit=50):
        # Request body for creating a form
        new_form = {
            "info": {
                "title": "Main Sprite Vote",
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

        collisions_file = open(collisions_file_name, 'r')
        self.collisions_json = json.load(collisions_file)
        if self.collisions_json is None:
            print(f"ERROR: Failed to load {collisions_file_name} as collision file. Check file name")
            return
        questions = []
        question_count = 0
        for collision_id in self.collisions_json:
            questions.append(self.format_question(collision_id, question_count))
            question_count += 1
            if question_count >= limit:
                break
        request_output = {
            "requests": []
        }
        for question in questions:
            print(question)
            print(request_output)
            request_output['requests'].append({"createItem": question})
        # Creates the initial form
        result = self.form_service.forms().create(body=new_form).execute()

        # Adds the question to the form
        self.form_service.forms().batchUpdate(formId=result["formId"], body=request_output).execute()

        # Prints the result to show the question has been added
        get_result = self.form_service.forms().get(formId=result["formId"]).execute()
        print(get_result)
        return

    def format_question(self, question_key, question_num):
        # sanity checks
        if question_key not in self.collisions_json:
            print(f"ERROR: key {question_key} is not in collisions dict - can't create poll question")
            return
        for subkey in ["new_files", "old_files"]:
            if subkey not in self.collisions_json[question_key]:
                print(f"ERROR: mis-formatted collisions json: f{question_key} does not contain {subkey}")
                return

        # by definition, new_files and old_files should never have a case where the count is equal to 0, so
        # no range checks are needed for the 0 index
        image_urls = [
            self.get_view_url_from_id(self.upload_image_to_drive(self.collisions_json[question_key]["old_files"][0])['id'])]
        for sprite_filename in self.collisions_json[question_key]['new_files']:
            image_urls.append(self.get_view_url_from_id(self.upload_image_to_drive(sprite_filename)['id']))
        print(image_urls)
        options_array = []
        for index in range(len(image_urls)):
            options_array.append({
                "value": "Current Main" if index == 0 else f"Option {index + 1}",
                "image": {"sourceUri": image_urls[index]},
            })

        new_question = {
            "item": {
                "title": self.get_title(question_key),
                "questionItem": {
                    "question": {
                        "required": False,
                        "choiceQuestion": {
                            "type": 'RADIO',
                            "options": options_array
                        }
                    }
                }
            },
            "location": {
                "index": question_num
            }
        }

        return new_question

    def upload_image_to_drive(self, image_filepath):
        if not self.creds or self.creds.invalid:
            flow = client.flow_from_clientsecrets(
                'F:/InfiniteFusion/GoogleAPIs/client_secret_813113044012-sbu2g7a10gsg6c9d3d80ghfdqejt8866.apps.googleusercontent.com.json',
                self.SCOPES)
            self.creds = tools.run_flow(flow, self.store)
        try:
            file_metadata = {'name': Path(image_filepath).name, 'parents': ["10xjZww_vnH-0Ju14gLzMjbl0lSHxfygd"]}
            media = MediaFileUpload(image_filepath, mimetype="image/png")
            out_file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return out_file
        except HttpError as error:
            print(f"ERROR: GoogleAPI: {error}")
        return None

    def get_title(self, question_key):
        return question_key

    def get_view_url_from_id(self, google_drive_id):
        if self.drive_service is None:
            return ""
        try:
            self.drive_service.permissions().create(fileId=google_drive_id, body={
                "role": "reader",
                "value": "anyone",
                "type": "anyone"
            }).execute()
            return f"https://drive.google.com/uc?id={google_drive_id}"
        except HttpError as error:
            print(f"ERROR: GoogleAPI: {error}")
        return ""


if __name__ == '__main__':
    form = GoogleForm()
    # form.upload_image_to_drive("F:/Folder Full of Nothing for dumping things/214.png")
    form.create_google_form("F:/InfiniteFusion/collision_text.json", limit=5)
