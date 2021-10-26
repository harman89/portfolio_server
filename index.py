import datetime
import random
import string
import xml.etree.ElementTree as ET
from os.path import dirname, join, realpath,exists

import flask
from flask import render_template, request, jsonify, flash, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from model import db, Lecture, app, User, Test, Question, Course, Answer, Group, InviteCode,GroupCourse,UserGroup,Marks,Part,Notification
import api

db.create_all()
login_manager = LoginManager(app)
login_manager.login_view = '/'

UPLOAD_FOLDER = 'data/uploads'
XML_FOLDER = 'data/xml'
ALLOWED_EXTENSIONS = {'doc', 'docx', 'pdf', 'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['XML_FOLDER'] = XML_FOLDER
class UserMarks(object):
    def __init__(self,user_id,theme,part_theme,mark,date, tries):
        self.user_id=user_id
        self.theme = theme
        self.part_theme = part_theme
        self.mark=mark
        self.date=date
        self.tries =tries

class ResultClass(object):
    def __init__(self, average, done, out_of):
        self.average = average
        self.done = done
        self.out_of = out_of

def create_XML_Test(test_id):
    test = db.session.query(Test).filter(Test.id == test_id).first()
    parts = db.session.query(Part).filter(Part.test_id==test_id).all()
    testRoot = ET.Element("test", theme = test.title)
    for part in parts:
        partElement = ET.SubElement(testRoot, "part", number = str(part.number),part_id = str(part.id))
        textPartElement = ET.SubElement(partElement, "text")
        textPartElement.text=part.text
        questions = db.session.query(Question).filter(Question.part_id==part.id).all()
        for question in questions:
            questionElement = ET.SubElement(partElement,"question",number = str(question.number+1))
            textQuestionElement = ET.SubElement(questionElement, "text")
            textQuestionElement.text = question.title
            answers = db.session.query(Answer).filter(Answer.question_id==question.id).all()
            answersElement = ET.SubElement(questionElement,"answers")
            for answer in answers:
                singleAnswerElement = ET.SubElement(answersElement,"answer", isTrue = str(answer.isTrue))
                answerTextElement = ET.SubElement(singleAnswerElement,"text")
                answerTextElement.text = answer.text
    tree = ET.ElementTree(testRoot)
    tree.write(join(dirname(realpath(__file__)),app.config['XML_FOLDER'])+"/"+test_id+".xml", encoding="UTF-8",xml_declaration=True)

#join(dirname(realpath(__file__)), app.config['UPLOAD_FOLDER']) + "/" + file.filename
def insert_xml():
    tree = ET.parse('zalog.xml')
    root = tree.getroot()
    print(root[0][0].text)
    for child in root:
        print(child.tag, child.attrib)
        for two in child:
            print(two.tag, two.attrib)

insert_xml()
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def insert_admin():
    if not db.session.query(User).filter(User.username == "admin").first():
        user = User(username="admin", name="admin", surname="admin", email="admin@admin.ru", role="admin")
        user.set_password("admin")
        db.session.add(user)
        db.session.commit()


insert_admin()
#create_XML_Test(1)

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


@app.route("/add_course", methods=['POST'])
@login_required
def add_course():
    if not db.session.query(Course).filter(Course.title == request.form.get("title")).first():
        title = request.form.get('title')
        course = Course(title=title)
        db.session.add(course)
        db.session.commit()
        return show_course_panel()
    else:
        return show_course_panel(message="Курс с таким именем уже существует !!!")


@app.route("/add_group_to_course", methods=['POST'])
@login_required
def add_groupcourse():
    course_id = request.form.get('course_id')
    if not db.session.query(GroupCourse).filter(GroupCourse.course_id==request.form.get('course_id')).filter(GroupCourse.group_id==request.form.get('group_id')).first():
        group_id = request.form.get('group_id')
        groupcourse = GroupCourse(group_id=group_id, course_id = course_id)
        db.session.add(groupcourse)
        db.session.commit()
        return show_course_overview(course_id,message="Группа успешно прикреплена к курсу")
    else:
        return show_course_overview(message="Эта группа уже прикреплена к курсу", course_id=course_id)


@app.route('/add_lecture', methods=['POST'])
@login_required
def add_lecture():
    course_id = request.form.get("course_id")
    course = db.session.query(Course).filter(Course.id == course_id).first()
    title = request.form.get('title')
    sub_title = request.form.get('sub_title')
    file = request.files['file']
    if file and allowed_file(file.filename):
        file.save(join(dirname(realpath(__file__)), app.config['UPLOAD_FOLDER']) + "/" + file.filename)
        print(join(dirname(realpath(__file__)), app.config['UPLOAD_FOLDER']) + "/" + file.filename)
        # file.save(app.config['UPLOAD_FOLDER'] + "/" + file.filename)
        lecture = Lecture(title=title,sub_title=sub_title, path_to_file=file.filename,
                          course=course)
        db.session.add(lecture)
        db.session.commit()
        return show_course_control_panel(course_id=course_id,
                                         message="Лекция успешно добавлена")
    else:
        return show_course_control_panel(course_id=course_id,
                                         message="Допустимые форматы pdf,doc,jpg,jpeg")


@app.route('/test<test_id>', methods=['GET', 'POST'])
@login_required
def show_test(test_id):
    course_id = request.form.get("course_id")
    if course_id is None:
        course_id = request.args.get("course_id")
    print(test_id)
    print(course_id)
    test = db.session.query(Test).filter(Test.id == test_id).first()
    parts = db.session.query(Part).filter(Part.test_id == test_id).all()
    return render_template("test.html", title=test.title, test_id =test_id, course_id=course_id, parts=parts)



@app.route('/part<part_id>', methods=['POST'])
@login_required
def show_part(part_id, message=""):
    course_id = request.form.get("course_id")
    test_id = request.form.get("test_id")
    if not part_id:
        part_id = request.form.get("part_id")
    print(test_id)
    print(course_id)
    print(part_id, "part")
    part = db.session.query(Part).filter(Part.id == part_id).first()
    print(part)
    if test_id is None:
        test_id=part.test_id
    if course_id is None:
        test = db.session.query(Test).filter(Test.id ==test_id).first()
        course_id = test.course_id
    count = 0
    for _ in part.question.all():
        count += 1
    return render_template("part.html", title=part.text, questions=part.question.all(), count=count,test_id =test_id, course_id=course_id, part_id = part_id)


@app.route('/lecture<lecture_id>', methods=['POST'])
@login_required
def show_lecture(lecture_id):
    course_id = request.form.get("course_id")
    lecture = db.session.query(Lecture).filter(Lecture.id == lecture_id).first()
    return render_template("lecture.html", lecture=lecture, course_id=course_id)


@app.route('/add_test', methods=['POST'])
def add_test():
    course_id = request.form.get("course_id")
    if not db.session.query(Test).filter(Test.title == request.form.get("title")).first():
        course = db.session.query(Course).filter(Course.id == course_id).first()
        test = Test(title=request.form.get("title"), course=course)
        test.close_date = datetime.datetime.strptime(request.form.get("close_date"), "%Y-%m-%d").date()
        db.session.add(test)
        db.session.commit()
        return show_course_control_panel(message="Тест успешно добавлен", course_id=course_id)
    else:
        return show_course_control_panel(message="Тест с таким именем уже существует !!!", course_id=course_id)


@app.route('/add_part', methods=['POST'])
def add_part():
    test_id = request.form.get("test_id")
    course_id = request.form.get("course_id")
    if not db.session.query(Part).filter(Part.text == request.form.get("title")).first():
        test = db.session.query(Test).filter(Test.id == test_id).first()
        number = db.session.query(Part).filter(Part.test_id==test_id).count()
        number=number+1
        part = Part(text=request.form.get("title"), test=test)
        part.number=number
        db.session.add(part)
        db.session.commit()
        return show_course_control_panel(message="Раздел теста успешно добавлен", course_id=course_id)
    else:
        return show_course_control_panel(message="Раздел теста с таким именем уже существует !!!", course_id=course_id)


@app.route('/add_question_in_part', methods=['POST'])
def add_question_in_part():
    part_id = request.form.get("part_id")
    print(part_id)
    part = db.session.query(Part).filter(Part.id == part_id).first()
    if part:
        count = 0
        for _ in part.question.all():
            count += 1
        question = Question(title=request.form.get(
            "question_title"), part=part, number = count)
        db.session.add(question)
        radio = request.form.get("radio")
        for i in range(1, 7):
            if request.form.get(f"answer{i}") != "":
                if radio == f"radio{i}":
                    db.session.add(Answer(text=request.form.get(
                    f"answer{i}"),question=question,isTrue = 1))
                else:
                    db.session.add(Answer(text=request.form.get(
                    f"answer{i}"),question=question,isTrue = 0))
        db.session.commit()
        return show_part(message="Вопрос успешно добавлен", part_id = part_id)
    else:
        return show_part(message="Ошибка",part_id = part_id)


@app.route("/edit_question_submit", methods=['POST'])
@login_required
def edit_question_submit():
    question_id = request.form.get("question_id")
    question = db.session.query(Question).filter(Question.id == question_id).first()
    part_id = question.part_id
    question.title = request.form.get("question_title")
    db.session.add(question)
    radio = request.form.get("radio")
    answers = db.session.query(Answer).filter(Answer.question_id == question.id).all()
    for answer in answers:
        answer.text = request.form.get(f"answer{answer.id}")
        if radio == f"radio{answer.id}":
            answer.isTrue = 1
        else:
            answer.isTrue = 0
        db.session.add(question)
    db.session.commit()
    return show_part(message="Вопрос успешно добавлен", part_id = part_id)


@app.route("/generate_invite_code", methods=['POST'])
@login_required
def generate_invite_code():
    flash("test")
    choice = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    for i in [i for i in list(string.ascii_uppercase)]:
        choice.append(i)
    code = ""
    for i in range(6):
        code += str(random.choice(choice))
    db.session.add(InviteCode(text=code))
    db.session.commit()
    return show_admin_panel(message=f"Код приглашения  - {code}")


@app.route("/generate_new_group", methods=['POST'])
@login_required
def generate_new_group():
    choice = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    for i in [i for i in list(string.ascii_lowercase + string.ascii_uppercase)]:
        choice.append(i)
    code = ""
    for i in range(6):
        code += str(random.choice(choice))
    question = Group(name=request.form.get("group_name"), code=code)
    db.session.add(question)
    db.session.commit()
    usergroup = UserGroup(group_id = question.id, user_id = current_user.id)
    print(usergroup.id,usergroup.group_id,usergroup.user_id)
    db.session.add(usergroup)
    db.session.commit()
    return show_groups_panel(message=f"Сгенерированный код - {code}")


@app.route('/')
def index(message=""):
    if current_user.is_authenticated:
        return show_course_panel()
    else:
        return render_template('login.html', message=message)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if flask.request.method == 'POST':
        if db.session.query(InviteCode).filter(InviteCode.text == request.form.get("invite_code")).first():
            user = User(username=request.form.get("username"), surname=request.form.get("surname"),
                        name=request.form.get("name"),
                        email=request.form.get("email"))
            user.set_password(request.form.get("password"))
            db.session.add(user)
            db.session.commit()
            return render_template('login.html', message="Успешная регистрация")
        else:
            return render_template('login.html', message="Неверный код приглашения")
    else:
        return render_template('registration.html')


@app.route('/registration_student', methods=['GET', 'POST'])
def registration_student():
    print(request.get_json())
    if flask.request.method == 'POST':
        request_for_registration = request.get_json()
        print(request_for_registration)
        group = db.session.query(Group).filter(Group.code==request_for_registration['code']).first()
        if group is not None:
            user = User(username=request_for_registration['username'], surname=request_for_registration['surname'],
                        name=request_for_registration['name'],
                        email=request_for_registration['mail'], role = "student")
            user.set_password(request_for_registration['password'])
            db.session.add(user)
            db.session.commit()
            usergroup = UserGroup(group_id=group.id, user_id=user.id)
            db.session.add(usergroup)
            db.session.commit()
            return jsonify({'message':'Registration completed'})
        else:
            return jsonify({'message':'invalid group code'})
    else:
        return jsonify({'message':'not post'})


@app.route('/exit')
@login_required
def logout():
    logout_user()
    return render_template('login.html')


@app.route("/admin")
def show_admin_panel(message=""):
    if current_user.is_authenticated:
        if current_user.role == "admin":
            users = db.session.query(User).all()
            return render_template("admin.html", users_list=users, message=message)
        else:
            return index(message="Отказано в доступе")
    else:
        return index(message="Отказано в доступе")


@app.route("/course_panel")
@login_required
def show_course_panel(message=""):
    course_list = db.session.query(Course).all()
    return render_template("course_panel.html", course_list=course_list, message=message)


@app.route("/notifications")
@login_required
def show_notifications(message=""):
    groups = db.session.query(UserGroup).filter(UserGroup.user_id==current_user.id).all()
    groups_list=[]
    if groups:
        for i in groups:
            group = db.session.query(Group).filter(Group.id == i.group_id).first()
            groups_list.append(group)
    notifications=[]
    if groups_list:
        for i in groups_list:
            notifications.append(db.session.query(Notification).filter(Notification.group_id==i.id).all())
    return render_template("notifications.html", message=message,zip=zip,notifications = notifications,groups_list=groups_list)


@app.route("/send_notification", methods=['POST'])
@login_required
def send_notification(message=""):
    text = request.form.get("notification_text")
    group_id = request.form.get("group_id")
    notification = Notification(text =text, date = datetime.datetime.now(), group_id=group_id)
    db.session.add(notification)
    db.session.commit()
    groups = db.session.query(UserGroup).filter(UserGroup.user_id==current_user.id).all()
    groups_list=[]
    if groups:
        for i in groups:
            group = db.session.query(Group).filter(Group.id == i.group_id).first()
            groups_list.append(group)
    notifications=[]
    if groups_list:
        for i in groups_list:
            notifications.append(db.session.query(Notification).filter(Notification.group_id==i.id).all())
    return render_template("notifications.html", message=message,zip=zip,notifications = notifications,groups_list=groups_list)


@app.route("/get_notifications", methods=['POST'])
def get_notifications():
    if flask.request.method == 'POST':
        request_info = request.data
        request_info = request_info.decode()
        user_id = request_info.strip("[]\"")
        user = db.session.query(User).filter(User.id == user_id).first()
        if user:
            usergroup = db.session.query(UserGroup).filter(UserGroup.user_id == user.id).first()
            group = db.session.query(Group).filter(Group.id == usergroup.group_id).first()
            notifications = db.session.query(Notification).filter(Notification.group_id==group.id).all()
            resultnotifications = []
            for nt in notifications:
                resultnotifications.append(nt.to_dict())
            return jsonify(resultnotifications)
        else:
            return jsonify({'message':'no such user'})
    else:
        return jsonify({'message':'not POST'})


@app.route("/groups_panel")
@login_required
def show_groups_panel(message=""):
    groups = db.session.query(UserGroup).filter(UserGroup.user_id==current_user.id).all()
    groups_list=[]
    if groups:
        for i in groups:
            group = db.session.query(Group).filter(Group.id == i.group_id).first()
            groups_list.append(group)
    return render_template("groups_panel.html", groups_list=groups_list, message=message)


@app.route("/edit_question<question_id>", methods=['POST'])
@login_required
def edit_question(question_id):
    course_id = request.form.get("course_id")
    test_id = request.form.get("test_id")
    question = db.session.query(Question).filter(Question.id == question_id).first()
    answers = db.session.query(Answer).filter(Answer.question_id == question.id).all()
    return render_template("edit_question.html", question = question, answers = answers, test_id = test_id, course_id = course_id)


@app.route("/students<group_id>", methods=['POST'])
@login_required
def show_group_list(group_id,message=""):
    group_id=request.form.get("group_id")
    group = db.session.query(Group).filter(Group.id == group_id).first()
    groupname = group.name
    grcourses = db.session.query(GroupCourse).filter(GroupCourse.group_id==group_id).all()
    courses = []
    if grcourses:
        for c in grcourses:
            course = db.session.query(Course).filter(Course.id==c.course_id).first()
            if course is not None:
                courses.append(course)
    studentsId = db.session.query(UserGroup).filter(UserGroup.group_id==group_id).all()
    partCount = 0
    
    tests = db.session.query(Test).all()
    parts = db.session.query(Part).all()
    allMarks = db.session.query(Marks).all()
    students = []
    marks = []
    if studentsId:
        for i in studentsId:
            student = db.session.query(User).filter(User.role=='student').filter(User.id==i.user_id).first()
            if student is not None:          
                students.append(student)
                for m in allMarks:
                    if(m.user_id == i.user_id):
                        marks.append(m)
    results=[]
    for stud in students:
        for mark in marks:
            if (stud.id==mark.user_id):
                for test in tests:
                    for part in parts:
                        if(mark.part_id==part.id):
                            if(part.test_id==test.id):
                                result = UserMarks(stud.id,test.title,part.text,mark.mark,mark.date,1)
                                results.append(result)
    #nu i bred ya napisal...
    #исправить отображение курсов
    todel = []
    for i in range(len(results)):
        for j in range(i+1,len(results)):
            if (results[i].user_id==results[j].user_id) and (results[i].theme==results[j].theme) and (results[i].part_theme==results[j].part_theme):
                if(results[i].date>results[j].date):
                    todel.append(j)
                    results[i].tries+=1
                    break
                else:
                    todel.append(i)
                    results[j].tries+=1
                    break
    newresults = []
    element_delete = True
    for i in range(len(results)):
        for j in todel:
            if(i==j):
                element_delete = False
                break
            else:
                continue
        if element_delete is not False:
            newresults.append(results[i])
        element_delete = True
    averages = []
    for stud in students:
        #print(stud.id)
        avg = 0
        counter = 0
        for i in range(len(newresults)):
            if(stud.id==newresults[i].user_id):
                avg+=int(newresults[i].mark[-2])
                counter+=1
        if(counter == 0):
            continue
        average = ResultClass(round((avg/counter),2),counter,len(parts))
        averages.append(average)
    print(averages)
    return render_template("marks.html", students=students, courses = courses, message=message,results = newresults, groupname = groupname, averages=averages)


@app.route("/course_control_panel<course_id>")
@login_required
def show_course_control_panel(course_id, message=""):
    tests = db.session.query(Test).filter(Test.course_id == course_id).all()
    lectures = db.session.query(Lecture).filter(Lecture.course_id == course_id).all()
    return render_template("course_control_panel.html", tests=tests, lectures=lectures, message=message,
                           course_id=course_id)


@app.route("/course<course_id>")
@login_required
def show_course_overview(course_id, message=""):
    tests = db.session.query(Test).filter(Test.course_id == course_id).all()
    lectures = db.session.query(Lecture).filter(Lecture.course_id == course_id).all()
    groups = db.session.query(UserGroup).filter(UserGroup.user_id==current_user.id).all()
    if groups:
        groups_list=[]
        for i in groups:
            group = db.session.query(Group).filter(Group.id == i.group_id).first()
            groups_list.append(group)
        return render_template("course_overview.html", tests=tests, lectures=lectures, course_id=course_id,groups = groups_list,message = message)
    else:
        return render_template("course_overview.html", tests=tests, lectures=lectures, course_id=course_id,groups = [],message = message)


@app.route("/delete_course<course_id>", methods=['POST'])
@login_required
def delete_course(course_id, message=""):
    course = db.session.query(Course).filter(Course.id == course_id).first()
    db.session.delete(course)
    db.session.commit()
    return show_course_panel()


@app.route('/educate')
def show_educate_page():
    if current_user.is_authenticated:
        return render_template('course_panel.html')
    else:
        return index(message="Отказано в доступе")


@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    user = db.session.query(User).filter(User.username == username).first()
    if user and user.check_password(password):
        login_user(user, remember=True)
        user.last_login_time = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
        return show_course_panel()
    else:
        return render_template("login.html", message="Ошибка авторизации")


@app.route('/login_student', methods=['GET', 'POST'])
def login_student():
    if flask.request.method == 'POST':
        request_for_login = request.get_json()
        username = request_for_login['username']
        password = request_for_login['password']
        user = db.session.query(User).filter(User.username == username).first()
        if user and user.check_password(password):
            user.last_login_time = datetime.datetime.now()
            db.session.add(user)
            db.session.commit()
            message = "Welcome"
            return jsonify(message=message,user_id=user.id)
        else:
            return jsonify({'message':'no such user'})
    else:
        return jsonify({'message':'not post'})


@app.route('/get_user_info', methods=['GET', 'POST'])
def get_user_info():
    if flask.request.method == 'POST':
        request_info = request.get_json()
        user_id = request_info['user_id']
        user = db.session.query(User).filter(User.id == user_id).first()
        if user:
            usergroup = db.session.query(UserGroup).filter(UserGroup.user_id == user.id).first()
            group = db.session.query(Group).filter(Group.id == usergroup.group_id).first()
            return jsonify(message = "success",name = user.name, surname = user.surname, group_name = group.name)
        else:
            return jsonify({'message':'error:('})
    else:
        return jsonify({'message':'not POST'})

@app.route('/get_lectures', methods=['GET', 'POST'])
def get_lectures():
    if flask.request.method == 'POST':
        request_info = request.data
        request_info = request_info.decode()
        user_id = request_info.strip("[]\"")
        user = db.session.query(User).filter(User.id == user_id).first()
        if user:
            usergroup = db.session.query(UserGroup).filter(UserGroup.user_id == user.id).first()
            group = db.session.query(Group).filter(Group.id == usergroup.group_id).first()
            groupcourse = db.session.query(GroupCourse).filter(GroupCourse.group_id == group.id).all()
            resultlections = []
            for gs in groupcourse:
                course = db.session.query(Course).filter(Course.id == gs.course_id).first()
                if course:
                    lections = db.session.query(Lecture).filter(Lecture.course_id==course.id).all()
                    for l in lections:
                        resultlections.append(l.to_dict())
            return jsonify(resultlections)
        else:
            return jsonify({'message':'no such user'})
    else:
        return jsonify({'message':'not POST'})

@app.route('/recieve_result', methods=['GET', 'POST'])
def recieve_result():
    if flask.request.method == 'POST':
        request_info = request.get_json()
        user_id = request_info['user_id']
        part_id = request_info['part_id']
        mark = request_info['result']
        date =datetime.datetime.now()
        mark = Marks(user_id = user_id, part_id = part_id, mark = mark, date = date)
        db.session.add(mark)
        db.session.commit()
        return jsonify({'message':'success'})
    else:
        return jsonify({'message':'not POST'})


@app.route('/get_test<test_id>', methods=['GET', 'POST'])
def get_test_info(test_id):
    if(exists(app.config['XML_FOLDER']+"/"+test_id+".xml")):
        create_XML_Test(test_id)
    return send_from_directory(app.config['XML_FOLDER'], test_id+".xml", as_attachment=True)


@app.route('/get_tests<user_id>', methods=['GET', 'POST'])
def get_tests(user_id):
    if flask.request.method == 'POST':
        user = db.session.query(User).filter(User.id == user_id).first()
        if user:
            usergroup = db.session.query(UserGroup).filter(UserGroup.user_id == user.id).first()
            group = db.session.query(Group).filter(Group.id == usergroup.group_id).first()
            groupcourse = db.session.query(GroupCourse).filter(GroupCourse.group_id == group.id).all()
            resulttests= []
            for gs in groupcourse:
                course = db.session.query(Course).filter(Course.id == gs.course_id).first()
                if course:
                    tests = db.session.query(Test).filter(Test.course_id==course.id).all()
                    print(tests)
                    for t in tests:
                        resulttests.append(t.id)
            print(resulttests)
            stringresult = ','.join(str(e) for e in resulttests)
            print(stringresult)
            return stringresult
        else:
            return jsonify({'message':'no such user'})
    else:
        return jsonify({'message':'not POST'})