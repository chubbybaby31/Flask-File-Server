import time
from flask import *
import os
import subprocess
import shutil
import zipfile
from _thread import start_new_thread

# create web app instance
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getcwd()

# handle root route
@app.route('/')
def root():
    app.config['UPLOAD_FOLDER'] = os.getcwd()

    return render_template('file_server.html', current_working_directory=os.getcwd(),
         file_list=subprocess.check_output('ls', shell=True).decode('utf-8').split('\n'), file='/static/image.png') # use 'dir' command on Windows

@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
      f = request.files['file']
      f.save(f.filename)
      return redirect('/')

@app.route('/return')
def return_to_fileserver():
    return redirect('/')
    
# handle 'cd' command
@app.route('/cd')
def cd():
    # run 'level up' command
    os.chdir(request.args.get('path'))
    
    # redirect to file manager
    return redirect('/')

# handle 'make directory' command
@app.route('/md')
def md():
    # create new folder
    os.mkdir(request.args.get('folder'))
    
    # redirect to fole manager
    return redirect('/')

# handle 'make directory' command
@app.route('/rm')
def rm():
    # remove certain directory
    shutil.rmtree(os.getcwd() + '/' + request.args.get('dir'))
    
    # redirect to fole manager
    return redirect('/')

@app.route('/rm_file')
def rm_file():
    path = os.getcwd() + '/' + request.args.get('file')
    os.remove(path)
    return redirect('/')
    
# view text files
@app.route('/view')
def view():
    # get the file content
    contents = ""
    if '.txt' in request.args.get('file') or '.py' in request.args.get('file') or '.json' in request.args.get('file'):
        with open(request.args.get('file')) as f:
            c = f.read()
        contents = c.split('\n')
    path = request.args.get('file')
    p = path.split('/File Server/')[1]
    return render_template('view.html', current_working_directory=os.getcwd(), file_list=subprocess.check_output('ls', shell=True).decode('utf-8').split('\n'), file=p, file_contents=contents)

@app.route('/download_file')
def download_file():
    path = request.args.get('path')
    return send_file(path, as_attachment=True)

@app.route('/download_folder')
def download_folder():
    folder = request.args.get('folder')
    path = os.getcwd() + '/' + folder
    temp_path = os.getcwd()
    name = folder + '.zip'
    handle = zipfile.ZipFile(name, 'w')
    os.chdir(path)
    for dir in os.listdir():
        handle.write(dir, compress_type=zipfile.ZIP_DEFLATED)
    
    handle.close()
    os.chdir(temp_path)

    start_new_thread(remove_zip, (path + '.zip',))

    return send_file(path + '.zip', as_attachment=True)

def remove_zip(path):
    print(path)
    time.sleep(2)
    os.remove(path)


# run the HTTP server
if __name__ == '__main__':
    app.run(debug=True, threaded=True)