import time
from flask import *
import os
import subprocess
import shutil
import zipfile
from _thread import start_new_thread

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getcwd()

trash_path = '/Users/Vishva/Documents/VSCode/Python/File Server/trash_bin'
trash_files = []

@app.route('/')
def root():
    cwd = os.getcwd()
    app.config['UPLOAD_FOLDER'] = cwd

    if 'trash_bin' in cwd:
        return render_template('trash_bin.html', current_working_directory=os.getcwd(),
         file_list=subprocess.check_output('ls', shell=True).decode('utf-8').split('\n'), file='/static/image.png')
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

@app.route('/restore')
def restore():
    src_path = request.args.get('path')
    compare_path = src_path + '\n'
    dst_path = ""
    for i in range(len(trash_files)):
        p = trash_files[i]
        if compare_path.__eq__(p.split(";*|")[1]):
            dst_path = p.split(";*|")[0]
            trash_files.pop(i)
            update_trash_file()
            break
    shutil.move(src_path, dst_path)
    return redirect('/')

@app.route('/cd')
def cd():
    os.chdir(request.args.get('path'))
    return redirect('/')

@app.route('/md')
def md():
    os.mkdir(request.args.get('folder'))
    return redirect('/')

@app.route('/rm_all')
def rm_all():
    cwd = os.getcwd()
    dirs = os.listdir(cwd)
    for dir in dirs:
        if '.' in dir and dir:
            os.remove(cwd + '/' + dir)
        elif dir:
            shutil.rmtree(cwd + '/' + dir)
    trash_files.clear()
    update_trash_file()

    return redirect('/')

@app.route('/rm')
def rm():
    src_path = os.getcwd() + '/' + request.args.get('dir')
    dirs = src_path.split('/')
    dst_path = ""
    for i in range(len(dirs)- 1):
        dst_path += dirs[i]
        if i < len(dirs) - 2:
            dst_path += '/'

    trash_files.append(dst_path + ";*|" + trash_path + '/' + request.args.get('dir') + '\n')
    update_trash_file()
    shutil.move(src_path, trash_path)
    return redirect('/')

@app.route('/rm_file')
def rm_file():
    src_path = os.getcwd() + '/' + request.args.get('file')
    dirs = src_path.split('/')
    dst_path = ""
    for i in range(len(dirs)- 1):
        dst_path += dirs[i]
        if i < len(dirs) - 2:
            dst_path += '/'

    trash_files.append(dst_path + ";*|" + trash_path + '/' + request.args.get('file') + '\n')
    update_trash_file()
    shutil.move(src_path, trash_path)
    return redirect('/')

@app.route('/rm_perm')
def rm_perm():
    path = os.getcwd() + '/' + request.args.get('dir')
    compare_path = path + '\n'
    shutil.rmtree(path)

    for i in range(len(trash_files)):
        p = trash_files[i].split(";*|")[1]
        if compare_path.__eq__(p):
            trash_files.pop(i)
            update_trash_file()
            print("removed")
            break

    return redirect('/')

@app.route('/rm_file_perm')
def rm_file_perm():
    path = os.getcwd() + '/' + request.args.get('file')
    compare_path = path + '\n'
    os.remove(path)

    for i in range(len(trash_files)):
        p = trash_files[i].split(";*|")[1]
        if compare_path.__eq__(p):
            trash_files.pop(i)
            update_trash_file()
            print("removed")
            break

    return redirect('/')
    
@app.route('/view')
def view():
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
    time.sleep(2)
    os.remove(path)

def update_trash_file():
    with open('/Users/Vishva/Documents/VSCode/Python/File Server/trash_file.txt', 'w') as f:
        f.truncate(0) # Delete file
        f.close()
    with open('/Users/Vishva/Documents/VSCode/Python/File Server/trash_file.txt', 'w') as f:
        f.writelines(trash_files) # Make new file and add paths from trash_files list
        f.close()

if __name__ == '__main__':
    app.run(debug=True, threaded=True)