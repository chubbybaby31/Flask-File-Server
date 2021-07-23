import time
from flask import *
import os
import subprocess
import shutil
import zipfile
from _thread import start_new_thread

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getcwd()

trash_path = os.getcwd() + "/trash_bin" # path to trash_bin directory
txt_trash_file_path = os.getcwd() + "/trash_file.txt" # path to txt file that stores the deleted file paths permenently
ip_url = "http://localhost:5000/uploader" # public/private ip_address for uploading files
trash_files = [] # array that is used to store the deleted file paths temperarily

# Making trash_bin directory if there isn't already one
try:
    os.mkdir("trash_bin")
    trash_path = os.getcwd + "/trash_bin"
except Exception:
    pass

# setting the trash_files array to hold the values in the txt file
try:
    with open(txt_trash_file_path, 'r') as f:
        content = f.readlines()
        for line in content:
            if ";*|" in line:
                trash_files.append(line)
except Exception:
    pass

# main page, file_server
@app.route('/')
def root():
    cwd = os.getcwd() # getting the current working directory
    app.config['UPLOAD_FOLDER'] = cwd # setting the upload folder

    file_list = subprocess.check_output('ls', shell=True).decode('utf-8').split('\n') # creating the file_list containing the files that will be displayed
    # Delete any file that we want to be invisible i.e. trash_bin and trash_file.txt
    for x in range(2):
        for i in range(len(file_list)):
            if "trash_bin" in file_list[i] or "trash_file.txt" in file_list[i]:
                file_list.pop(i)
                break
    
    # If in the trash directory, render a modified template for it.
    if 'trash_bin' in cwd:
        return render_template('trash_bin.html', current_working_directory=cwd,
         file_list=file_list, file='/static/image.png')
    return render_template('file_server.html', current_working_directory=cwd,
         file_list=file_list, file='/static/image.png', trash_path=trash_path, ip_url=ip_url)

# uploading files
@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
        f = request.files['file']
        f.save(f.filename)
        return redirect('/')

# returning from viewing a file back to normal fileserver template
@app.route('/return')
def return_to_fileserver():
    return redirect('/')

# restoring folders or files from trash_bin
@app.route('/restore')
def restore():
    src_path = request.args.get('path')
    compare_path = src_path + '\n'
    dst_path = ""
    for i in range(len(trash_files)):
        p = trash_files[i]
        if compare_path.__eq__(p.split(";*|")[1]):
            dst_path = p.split(";*|")[0]
            trash_files.pop(i) # deleting file from array
            update_trash_file() # deleting file from txt
            break
    shutil.move(src_path, dst_path)
    return redirect('/')

# change directory
@app.route('/cd')
def cd():
    os.chdir(request.args.get('path'))
    print(os.getcwd())
    return redirect('/')

# make new directory
@app.route('/md')
def md():
    os.mkdir(request.args.get('folder'))
    return redirect('/')

# remove all files from trash_bin
@app.route('/rm_all')
def rm_all():
    cwd = os.getcwd()
    dirs = os.listdir(cwd)
    for dir in dirs:
        if '.' in dir and dir:
            os.remove(cwd + '/' + dir)
        elif dir:
            shutil.rmtree(cwd + '/' + dir)
    trash_files.clear() # clearing the trash_files array
    update_trash_file() # clearing the txt file

    return redirect('/')

# moving folder to trash
@app.route('/rm')
def rm():
    src_path = os.getcwd() + '/' + request.args.get('dir')
    dirs = src_path.split('/')
    dst_path = ""
    for i in range(len(dirs)- 1):
        dst_path += dirs[i]
        if i < len(dirs) - 2:
            dst_path += '/'

    trash_files.append(dst_path + ";*|" + trash_path + '/' + request.args.get('dir') + '\n') # Adding the folder path to the array and txt file
    update_trash_file()
    shutil.move(src_path, trash_path) # moving folder to trash
    return redirect('/')

# moving files to trash
@app.route('/rm_file')
def rm_file():
    src_path = os.getcwd() + '/' + request.args.get('file')
    dirs = src_path.split('/')
    dst_path = ""
    for i in range(len(dirs)- 1):
        dst_path += dirs[i]
        if i < len(dirs) - 2:
            dst_path += '/'

    trash_files.append(dst_path + ";*|" + trash_path + '/' + request.args.get('file') + '\n') # Adding the file path to the array and txt file
    update_trash_file()
    shutil.move(src_path, trash_path) # moving file to trash
    return redirect('/')

# removing folder permenently (removing from trash_bin)
@app.route('/rm_perm')
def rm_perm():
    path = os.getcwd() + '/' + request.args.get('dir')
    compare_path = path + '\n' # compare to the array paths (they have a new line character after them)
    shutil.rmtree(path) # removing folder

    # removing folder from array and txt file
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
    compare_path = path + '\n' # compare to the array paths (they have a new line character after them)
    os.remove(path) # removing file

    # removing path from array and txt file
    for i in range(len(trash_files)):
        p = trash_files[i].split(";*|")[1]
        if compare_path.__eq__(p):
            trash_files.pop(i)
            update_trash_file()
            print("removed")
            break

    return redirect('/')

# viewing the file
@app.route('/view')
def view():
    contents = ""
    if '.txt' in request.args.get('file') or '.py' in request.args.get('file') or '.json' in request.args.get('file'):
        with open(request.args.get('file')) as f:
            c = f.read()
        contents = c.split('\n') # array of the lines of the txt file. If no split the view template will put everythin on one line
    path = request.args.get('file')
    p = path.split('/File Server/')[1] # getting the local path of the file, change to "Flask-File-Server" if cloned from github
    return render_template('view.html', current_working_directory=os.getcwd(), file_list=subprocess.check_output('ls', shell=True).decode('utf-8').split('\n'), file=p, file_contents=contents)

# downloading file
@app.route('/download_file')
def download_file():
    path = request.args.get('path')
    return send_file(path, as_attachment=True)

# downloading folder
@app.route('/download_folder')
def download_folder():
    folder = request.args.get('folder')
    path = os.getcwd() + '/' + folder
    temp_path = os.getcwd()
    name = folder + '.zip'
    handle = zipfile.ZipFile(name, 'w') # creating zip file
    os.chdir(path)
    for dir in os.listdir():
        handle.write(dir, compress_type=zipfile.ZIP_DEFLATED) # adding all files in folder to zipfile
    
    handle.close()
    os.chdir(temp_path)

    start_new_thread(remove_zip, (path + '.zip',)) # deleting zipfile after sending. new thread is used so we send the file first then delete

    return send_file(path + '.zip', as_attachment=True)

# remove the zipfile from above function
def remove_zip(path):
    time.sleep(2) # wait for zipfile to be downloaded
    os.remove(path) # remove zipfile

# change the contents of the txt file to match the elements in the trash_files array
def update_trash_file():
    with open(txt_trash_file_path, 'w') as f:
        f.truncate(0) # Delete txt file
        f.close()
    with open(txt_trash_file_path, 'w') as f:
        f.writelines(trash_files) # Make new txt file and add paths from trash_files list
        f.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0' ,debug=True, threaded=True)