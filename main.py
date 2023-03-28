import utils
import requests
from exporter import Exporter

user_data = utils.get_json_from_file("userdata.json")

session_requests = requests.session()
payload = {
    "email": user_data['bookstack']['login'],
    "password": user_data['bookstack']['password'],
    "_token": user_data['bookstack']['token']
}
login_url = user_data['bookstack']['url'] + "/login"
payload["_token"] = utils.get_authenticity_token(session_requests, login_url)
login_result = utils.login(session_requests, login_url, payload)

exporter = Exporter(session_requests, user_data)
exporter.export_shelves()
exporter.import_shelves()
exporter.export_books()
exporter.import_books()
exporter.export_pages()
exporter.parse_pages()
#exporter.filter_similar_pages()
exporter.import_pages()
