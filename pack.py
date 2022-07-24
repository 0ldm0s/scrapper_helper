import os
import shutil


def walk():
    root_path = os.path.abspath(os.path.dirname(__file__))
    g = os.walk(root_path)
    for path, _, file_list in g:
        for file_name in file_list:
            file_name = str(file_name).strip()
            full_name = os.path.join(path, file_name)
            if full_name.find('__pycache__') < 0:
                continue
            if full_name.find('pack.pyc') >= 0:
                continue
            target_path = os.path.abspath(path + '/../')
            base_file_name = file_name[:file_name.index('.')]
            target_file_name = '{}.pyc'.format(base_file_name)
            original_file_name = '{}.py'.format(base_file_name)
            target_full_name = os.path.join(target_path, target_file_name)
            original_full_name = os.path.join(target_path, original_file_name)
            print(target_full_name)
            shutil.move(full_name, target_full_name)
            os.unlink(original_full_name)
    g = os.walk(root_path)
    for path, _, _ in g:
        if path.find('__pycache__') >= 0:
            print(path)
            shutil.rmtree(path)


if __name__ == '__main__':
    walk()
