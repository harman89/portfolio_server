from flask import send_from_directory, jsonify

from index import app, db
from model import Lecture, Test

@app.route('/get_lecture<lecture_id>', methods=['GET', 'POST'])
def get_lecture_file(lecture_id):
    lecture = db.session.query(Lecture).filter(Lecture.id == lecture_id).first()
    return send_from_directory(app.config['UPLOAD_FOLDER'], lecture.path_to_file, as_attachment=True)

