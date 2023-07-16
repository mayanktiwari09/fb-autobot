#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import requests
from facepy import GraphAPI
import configparser
import json
import sys
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLineEdit

config_file = 'fb_config.ini'
post_file = 'post.json'


class MainWindow(QMainWindow):
    def __init__(self,sections):
        super().__init__()

        self.setWindowTitle("Facebook Post Upload")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        access_token_label = QLineEdit()
        access_token_label.setPlaceholderText("Access Token")
        layout.addWidget(access_token_label)
        self.access_token_label = access_token_label

        message_label = QLineEdit()
        message_label.setPlaceholderText("Message")
        layout.addWidget(message_label)
        self.message_label = message_label

        select_images_button = QPushButton("Select Images")
        select_images_button.clicked.connect(self.handle_select_images)
        layout.addWidget(select_images_button)

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.handle_submit)
        layout.addWidget(submit_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.sections = sections
        self.image_urls = []

    def handle_select_images(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Image files (*.jpg *.jpeg *.png)")
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            self.image_urls = selected_files

    def handle_submit(self):
        access_token = self.access_token_label.text()
        message = self.message_label.text()

        print(f"Access Token: {access_token}")
        print(f"Message: {message}")
        print(f"Image URLs: {self.image_urls}")

        def make_post(access_token_entry, message_entry, image_urls_entry, sections):
            access_token = access_token_entry.strip()
            message = message_entry
            image_urls = image_urls_entry
            fb = FbPageAPI(access_token)
            for index, section in enumerate(sections):
                page_info = config_section_map(section)
                print(index + 1, page_info)
                # get page token
                page_access_token = fb.get_page_access_token(_page_id=page_info['page_id'])
                fb.upload_images_and_create_post(access_token=page_access_token,
                                                 page_id=page_info['page_id'],
                                                 album_name='Mobile uploads',
                                                 message=message,
                                                 image_urls=image_urls)
        make_post(access_token,message,self.image_urls,self.sections)

class FbPageAPI:
    def __init__(self, _access_token, limit=250):
        self.access_token = _access_token
        self.graph = GraphAPI(self.access_token)
        self.accounts = self._get_accounts(limit)

    def _get_accounts(self, limit=250):
        self.accounts = self.graph.get('me/accounts?limit=' + str(limit))
        return self.accounts['data']

    def get_accounts(self):
        return self.accounts['data']

    def get_page_access_token(self, _page_id):
        """
            :param _page_id:
            :return: page_specific_token
        """
        for data in self.accounts:
            if _page_id == data['id']:
                _page_access_token = data['access_token']
                # print('access_token: ', _page_access_token)
                print('')
                print('Page id: ', data['id'])
                print('Page Name: ', data['name'])
                return _page_access_token
        else:
            return None

    @staticmethod
    def upload_images_and_create_post(access_token, page_id, album_name, message, image_urls):
        # Find album ID by name
        def get_album_id_by_name():
            url = "https://graph.facebook.com/v12.0/me/albums"
            params = {
                "access_token": access_token
            }
            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                for album in data['data']:
                    if album['name'] == album_name:
                        return album['id']
            else:
                print("Failed to retrieve album IDs. Error:", response.json())

            return None

        album_id = get_album_id_by_name()
        if not album_id:
            print("Album not found.")
            return

        # Upload images to album
        upload_url = f"https://graph.facebook.com/v12.0/me/photos"
        upload_params = {
            "access_token": access_token,
            "published": "false"
        }

        imageIds = []

        for image_url in image_urls:
            upload_file = [("source", open(image_url, "rb"))]
            response = requests.post(upload_url, params=upload_params, files=upload_file)
            if response.status_code == 200:
                data = response.json()
                imageIds.append(data['id'])

        if len(imageIds) > 0:
            image_ids = imageIds
            # Create post with uploaded images
            post_url = "https://graph.facebook.com/" + page_id + "/feed"

            attached_media = [{"media_fbid": image_id} for image_id in image_ids]

            post_params = {
                "access_token": access_token,
                "message": message,
                "attached_media": json.dumps(attached_media)
            }

            args = dict()
            args["message"] = message
            for img_id in image_ids:
                key = "attached_media[" + str(image_ids.index(img_id)) + "]"
                args[key] = "{'media_fbid': '" + img_id + "'}"
            url = f"https://graph.facebook.com/me/feed?access_token=" + access_token
            post_response = requests.post(url, data=args)

            if post_response.status_code == 200:
                print("Post created successfully!")
            else:
                print("Failed to create the post. Error:", post_response.json())
        else:
            print("Failed to upload images to the album")



    @staticmethod
    def post_in_page(page_access_token, page_id, image_file=None, message=None):
        """
             Method to post the media and text message to your page you manage.
             :param page_access_token: valid api token
             :param page_id: Your page id
             :param image_file: Image File along with path
             :param message: Text
             :return: None
         """
        try:
            page_graph = GraphAPI(page_access_token)

            print('Posting .....')
            if image_file:
                image_file = open(image_file,'rb')
                image_ids = ['213517658333850', '213517731667176']
                media = [{"media_fbid": image_id} for image_id in image_ids]
                if message:
                    page_graph.post(path=page_id + '/feed', message=message, attached_media=json.dumps(media))
                else:
                    page_graph.post(path=page_id + '/photos', source=image_file)
            else:
                if not message:
                    message = 'Hello everyone!!'
                page_graph.post(path=page_id + '/feed', message=message)
            print('Posted Successfully !! ..')
        except Exception as error:
            print('Posting failed .. ', str(error))


if __name__ == '__main__':
    config = configparser.ConfigParser()

    config.read(config_file)
    # get sections
    sections = config.sections()
    print('Config sections - ', sections)

    def config_section_map(_section):
        dict1 = {}
        options = config.options(_section)
        for option in options:
            try:
                dict1[option] = config.get(_section, option)
                if dict1[option] == -1:
                    print("skip: %s" % option)
            except:
                print("exception on %s!" % option)
                dict1[option] = None
        return dict1

    postDetails = json.load(open(post_file))
    app = QApplication(sys.argv)
    window = MainWindow(sections)
    window.show()
    sys.exit(app.exec_())



