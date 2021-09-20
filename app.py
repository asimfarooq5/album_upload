import os
import os.path as op

import werkzeug
from flask import Flask, render_template, session, redirect, request
from flask_restful import Api, reqparse, Resource
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

image_path = op.join(op.dirname(__file__), "images")
try:
    os.mkdir(image_path)
except OSError:
    pass
UPLOAD_FOLDER = image_path


class Package(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.String(50), nullable=True)
    image = db.Column(db.String(50), nullable=True)


app = Flask(__name__, static_folder='')
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

api = Api(app)
db.init_app(app)
db.create_all(app=app)

image_path = op.join(op.dirname(__file__), "images")


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'password':
            error = 'Invalid Credentials. Please try again.'
        else:
            session['logged_in'] = True
            return redirect('/')
    return render_template('login.html', error=error)


@app.route('/', methods=['GET', 'POST'])
def table():
    if session['logged_in'] == True:
        packages = Package.query.all()
        return render_template("package.html", packages=packages)
    return render_template('login.html')


@app.route('/package/<p_id>', methods=['GET'])
def package(p_id):
    if session['logged_in'] == True:
        package = Package.query.filter_by(package_id=p_id).first()
        files = package.image.split("-")
        return render_template("image.html", files=files)
    return render_template('login.html')


class PackageResource(Resource):
    def post(self):
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('package_id', type=str, help='Package ID', required=True)
        parser.add_argument('image', help='Captured Image', type=werkzeug.datastructures.FileStorage,
                            location='files', required=False, action='append')
        args = parser.parse_args(strict=True)
        count = 1
        filename = ''
        package = Package()
        if args['image']:
            images = args['image']
            for image in images:
                new_filename = str(count) + "_" + args['package_id'] + "_" + image.filename
                image.save(os.path.abspath(os.path.join(image_path, new_filename)))
                count += 1
                filename = filename + "-" + new_filename

            package.package_id = args['package_id']
            package.image = filename[1:]
            db.session.add(package)
            db.session.commit()
        return {"messgae": "Upload Done"}, 201


@app.route('/logout')
def logout():
    session['logged_in'] = False
    return render_template('login.html')


api.add_resource(PackageResource, '/api/upload_package/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
