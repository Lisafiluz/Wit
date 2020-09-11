import datetime
from distutils.dir_util import copy_tree
import filecmp
import fileinput
import os
from pathlib import Path
import random
import shutil
import sys
from time import gmtime, strftime

import matplotlib.pyplot as plt
import networkx as nx


LOG_PATH = Path.home() / ".wit" / "log.txt"
WIT_PATH = Path.home() / ".wit"
STAGING_AREA_PATH = Path.home() / ".wit" / "staging_area"
IMAGES_PATH = Path.home() / ".wit" / "images"
REFERENCES_PATH = Path.home() / ".wit" / "references.txt"
ACTIVATED_PATH = Path.home() / ".wit" / "activated.txt" 


def log(message: str) -> None:
    time = datetime.datetime.now()
    log_to_add = f"{time} : {message}\n"
    try:
        if not LOG_PATH.exists():
            with open(LOG_PATH, "w+") as log_file:
                log_file.write(log_to_add)
        else:
            with open(LOG_PATH, "a") as log_file:
                log_file.write(log_to_add)
    except FileNotFoundError:
        raise


def init() -> None:
    WIT_PATH.mkdir()
    STAGING_AREA_PATH.mkdir()
    IMAGES_PATH.mkdir()
    try:
        with open(ACTIVATED_PATH, "w+") as activated_file:
                activated_file.write("master")
    except Exception as err:
        log(err)
    else:
        log("Success - .wit directory created with images and staging_area sub-directories; activated.txt file created")


def is_wit_dir_in_path(path: Path) -> bool:
    parents = list(path.parents)
    for parent in parents:
        if WIT_PATH in list(parent.iterdir()):
            return True 
    return False


def add(path: str) -> None:
    new_path = Path(path).absolute()
    if new_path.is_dir() or new_path.is_file():
        if new_path.exists():
            if is_wit_dir_in_path(new_path):
                parents = list(new_path.parents)
                start_creation = False
                in_dir = STAGING_AREA_PATH
                for parent in parents[-1::-1]:
                    if start_creation:
                        in_dir = in_dir / parent.name
                        if not in_dir.exists():
                            in_dir.mkdir()
                    if WIT_PATH in list(parent.iterdir()):
                        start_creation = True
                try:
                    if new_path.is_file():
                        file_name = in_dir / new_path.name
                        shutil.copyfile(path, str(file_name))
                    else:
                        directory_name = in_dir / new_path.name
                        copy_tree(path, str(directory_name))
                    
                except Exception as err:
                    log(f"Error - {err}")
                
            else:
                log(f"Error - wit directory not found in -> {path}")
        else:
            log(f"Error - no file / directory in path -> {path}")
    else:
        log(f"Error - invalid path -> {path}")


def get_commit_id() -> str:
    characthers = "1234567890abcdef"
    length = 40
    commit_id = ''.join(random.choice(characthers) for _ in range(length))
    return commit_id


def get_parent():
    if not REFERENCES_PATH.exists():
        return None
    else:
        try:
            with open(str(REFERENCES_PATH), 'r') as file:
                file_txt = file.readlines()
        except PermissionError as err:
            log(err)
        else:
            parent_head = file_txt[0][file_txt[0].find("=") + 1:-1]
            return parent_head


def create_metadata_file(commit_id: str, message: str, images_path: Path, optional_commit_after_merge_branch_id) -> None:
    text_to_add = ""
    parent = get_parent()
    if not optional_commit_after_merge_branch_id:
        row1 = f"parent={parent}\n"
    else:
        row1 = f"parent={parent},{optional_commit_after_merge_branch_id}\n"
    time_zone = strftime("%z", gmtime())
    time = datetime.datetime.now().strftime(f"%a %b %d %X %Y{time_zone}")
    row2 = f"date={time}\n"
    row3 = f"message={message}\n"
    text_to_add += row1
    text_to_add += row2
    text_to_add += row3
    file_name = commit_id + ".txt"
    file_path = images_path / file_name
    try:
        with open(file_path, 'w+') as file_handler:
            file_handler.write(text_to_add)
    except PermissionError as err:
        log(err)


def copy_content(source_dir: Path, dest_dir: Path) -> None:
    try:
        copy_tree(str(source_dir), str(dest_dir))
    except Exception as err:
        log(err)


def get_activated_branch() -> str:
    try:
        with open(str(ACTIVATED_PATH), 'r') as activated_file:
            return activated_file.read()
    except Exception as err:
        log(err)
        return ""


def update_references_file(commit_id: str) -> None:
    if not REFERENCES_PATH.exists():
        try:
            file = open(str(REFERENCES_PATH), 'w+')
            file.write("HEAD=\nmaster=\nname=\n")
        except PermissionError as err:
            print(err)
        finally:
            file.close()
    activated_branch = get_activated_branch()
    try:
        with open(str(REFERENCES_PATH), 'r') as reference_file:
            references_file_lines = reference_file.readlines()
    except Exception as err:
        log(err)
    else:
        update_branch_commit_id = references_file_lines[2][:references_file_lines[2].find('=')] == activated_branch
        update_master_commit_id = activated_branch == "master"

        references_file_lines[0] = references_file_lines[0][:5] + commit_id + "\n"  # new HEAD line
        if update_master_commit_id:
            references_file_lines[1] = references_file_lines[1][:7] + commit_id + "\n"  # new master line
        if update_branch_commit_id:
            references_file_lines[2] = f"{activated_branch}={commit_id}\n"
        try:
            with open(str(REFERENCES_PATH), 'w') as reference_file_add:
                reference_file_add.writelines(references_file_lines)
        except Exception as err:
            log(err)


def commit(message: str, optional_commit_after_merge_branch_id=None) -> None:
    cwd_path = Path.cwd().absolute()
    if is_wit_dir_in_path(cwd_path):
        commit_id = get_commit_id()
        commit_path = IMAGES_PATH / commit_id
        if not commit_path.exists():
            commit_path.mkdir()
            create_metadata_file(commit_id, message, IMAGES_PATH, optional_commit_after_merge_branch_id)
            copy_content(STAGING_AREA_PATH, commit_path)
            update_references_file(commit_id)
        else:
            commit(message)  # Until we get diffrent commit id
    else:
        log(f"Error - wit directory not found in -> {cwd_path}")


def get_list_of_files_tree(path: str):
    files_path_list = []
    for root, _dir, files in os.walk(path):
        for file in files:
            files_path_list.append(str(Path(root.replace(path, "")) / file))
    return files_path_list


def get_head_id() -> str:
    head_id = ""
    if REFERENCES_PATH.exists():
        try:
            with open(REFERENCES_PATH, 'r') as references_file:
                head_line = references_file.readlines()[0]
        except PermissionError as err:
            log(err)
        else:
            head_id = head_line[5:-1]
            return head_id
    else:
        log("Error - References file doesn't exist; do commit")
    return head_id


def get_head_tree_path(head_id: str) -> str:
    return str(IMAGES_PATH / head_id)
   

def get_changes_to_be_commited(head_id: str) -> str:
    head_tree_path = get_head_tree_path(head_id) 
    head_tree = get_list_of_files_tree(head_tree_path)
    stage_tree = get_list_of_files_tree(str(STAGING_AREA_PATH))
    changes = set(stage_tree).difference(set(head_tree))
    if ".DS_Store" in changes:  # operation system hidden file
        changes.remove(".DS_Store")
    return " \n".join(changes)


def get_orginal_path() -> str:
    lisr_dir_in_stage = os.listdir(str(STAGING_AREA_PATH))
    for directory in lisr_dir_in_stage:
        if directory[0] != ".":
            return str(Path.home() / directory)
    log("Error - orginal path not found")
    return "orginal$not$found"


def get_first_staging_area_path() -> str:
    lisr_dir_in_stage = os.listdir(str(STAGING_AREA_PATH))
    for directory in lisr_dir_in_stage:
        if directory[0] != ".":
            return str(STAGING_AREA_PATH / directory)
    log("Error - staging_area path not found")
    return "staging_area$not$found"


def get_relative_path_for_staging(full_path: Path, orginal_path: str, staging_area_first_path: str) -> Path:
    full_path_staging = Path(staging_area_first_path + str(full_path).replace(orginal_path, ""))
    return full_path_staging


def get_not_staged_files() -> str:
    orginal_path = get_orginal_path()
    staging_area_first_path = get_first_staging_area_path()
    if orginal_path != "orginal$not$found" and staging_area_first_path != "orginal$not$found":
        not_staged_files = []
        if Path(staging_area_first_path).exists():
                    diff_files = filecmp.dircmp(str(orginal_path), str(staging_area_first_path)).diff_files
                    for diff_file in diff_files:
                        if diff_file[0] != '.':
                            not_staged_files.append(diff_file)
        for root, dirs, _files in os.walk(str(orginal_path)):
            for sub_dir in dirs:
                full_path = Path(root) / sub_dir
                full_path_staging = get_relative_path_for_staging(full_path, orginal_path, staging_area_first_path)
                if full_path_staging.exists():
                    diff_files = filecmp.dircmp(str(full_path), str(full_path_staging)).diff_files
                    for diff_file in diff_files:
                        if diff_file[0] != '.':
                            not_staged_files.append(diff_file)
        not_staged_files_clear = [not_staged_file for not_staged_file in not_staged_files if not_staged_file != ".DS_Store"]
        return " ".join(not_staged_files_clear)

    else:
        return "Error occurs while getting orginal folder path or staging area path - check the log file"


def get_untracked_files(head_id: str) -> str:
    orginal_path = get_orginal_path()
    staging_area_first_path = get_first_staging_area_path()
    if orginal_path != "orginal$not$found" and staging_area_first_path != "orginal$not$found":
        untracked_files = []
        if Path(staging_area_first_path).exists():
                    only_on_orginal_files = filecmp.dircmp(str(orginal_path), str(staging_area_first_path)).left_only
                    for file in only_on_orginal_files:
                        untracked_files.append(file)
        for root, dirs, _files in os.walk(str(orginal_path)):
            for sub_dir in dirs:
                full_path = Path(root) / sub_dir
                full_path_staging = get_relative_path_for_staging(full_path, orginal_path, staging_area_first_path)
                if full_path_staging.exists():
                    only_on_orginal_files = filecmp.dircmp(str(full_path), str(full_path_staging)).left_only
                    for file in only_on_orginal_files:
                        untracked_files.append(file)
                else:
                    for _root2, _dirs2, files2 in os.walk(str(full_path)):
                        for file2 in files2:
                            untracked_files.append(file2)
        return " ".join(untracked_files)
    else:
        return "Error occurs while getting orginal folder path or staging area path - check the log file"


def status():
    cwd_path = Path.cwd().absolute()
    if is_wit_dir_in_path(cwd_path):
        message = ""
        head_id = get_head_id()
        message += f"Current commit id (HEAD): {head_id}\n"
        message += f"Changes to be commited: {get_changes_to_be_commited(head_id)}\n"
        message += f"Changes not staged for commit: {get_not_staged_files()}\n"
        message += f"Untracked files: {get_untracked_files(head_id)}"
        print(message)
    else:
        log(f"Error - wit directory not found in -> {cwd_path}")


def get_master_id() -> str:
    master_id = ""
    if REFERENCES_PATH.exists():
        try:
            with open(REFERENCES_PATH, 'r') as references_file:
                master_line = references_file.readlines()[1]
        except PermissionError as err:
            log(err)
        else:
            master_id = master_line[7:-1]
            return master_id
    else:
        log("Error - References file doesn't exist; do commit")
    return master_id


def copy_commit_id_content_to_orginal_path(commit_id: str) -> None:
    orginal_path = Path(get_orginal_path())
    shutil.rmtree(orginal_path)
    commit_id_path = IMAGES_PATH / commit_id
    shutil.copytree(str(commit_id_path), str(Path.home()))


def copy_commit_id_to_staging_area(commit_id: str) -> None:
    shutil.rmtree(str(STAGING_AREA_PATH))
    commit_id_path = IMAGES_PATH / commit_id
    shutil.copytree(str(commit_id_path), str(STAGING_AREA_PATH))


def update_head_references_file(commit_id: str) -> None:
    if REFERENCES_PATH.exists():
        for line in enumerate(fileinput.input(str(REFERENCES_PATH), inplace=1)):
            if line[1][:line[1].find('=')] == "HEAD":
                sys.stdout.write(line[1][:line[1].find('=') + 1] + commit_id)
                sys.stdout.write("\n")
            else:
                sys.stdout.write(line[1])
    else:
        log(f"Error - references file not found on path {REFERENCES_PATH}")


def update_activated_file() -> None:
    try:
        with open(str(REFERENCES_PATH), 'r') as references_file:
            references_file_lines = references_file.readlines()
    except Exception as err:
        log(err)
    else:
        if len(references_file_lines) == 3:  # there is branch to activate
            branch_name = references_file_lines[2][:references_file_lines[2].find('=')]
            try:
                with open(str(ACTIVATED_PATH), 'w') as activated_file:
                    activated_file.write(branch_name)
            except Exception as err:
                log(err)


def checkout(commit_id: str) -> None:
    cwd_path = Path.cwd().absolute()
    if is_wit_dir_in_path(cwd_path):
        head_id = get_head_id()
        if get_changes_to_be_commited(head_id) == "" and get_not_staged_files() == "":
            if commit_id == "master":
                commit_id = get_master_id()
            else:
                try:
                    with open(str(REFERENCES_PATH), 'r') as references_file:
                        references_file_lines = references_file.readlines()
                except Exception as err:
                    log(err)
                else:
                    if len(references_file_lines) == 3:  # there is branch to get his commit_id
                        branch_name = references_file_lines[2][:references_file_lines[2].find('=')]
                        if commit_id == branch_name:
                            commit_id = references_file_lines[2][references_file_lines[2].find('=') + 1:-1]

            copy_commit_id_content_to_orginal_path(commit_id)
            copy_commit_id_to_staging_area(commit_id)
            update_head_references_file(commit_id)
            update_activated_file()
        else:
            log("Error - there is changed files or new files in original path, the operation is invalid; Do add or commit before checkout")
    else:
        log(f"Error - wit directory not found in -> {cwd_path}")


def get_parent_id(file_id: str) -> str:
    file_name = file_id + ".txt"
    file_path = IMAGES_PATH / file_name
    try:
        with open(str(file_path), 'r') as file:
            file_txt = file.readlines()
            return file_txt[0][7:-1]  # ex. parent=0000000\n
    except Exception as err:
        log(err)
        return "None"


def get_commits_edges() -> list:
    chars_to_show = 6
    edges = []
    head_id = get_head_id()
    master_id = get_master_id()
    edges.append(('head', head_id[:chars_to_show]))
    edges.append(('master', master_id[:chars_to_show]))
    child_id = head_id
    parent_id = get_parent_id(head_id)
    while parent_id != "None":
        parents = parent_id.split(',')
        for parent in parents:
            edges.append((child_id[:chars_to_show], parent[:chars_to_show]))
            
        child_id = parents[0]  # continue with heads
        parent_id = get_parent_id(parents[0])
    return edges


def graph() -> None:
    cwd_path = Path.cwd().absolute()
    if is_wit_dir_in_path(cwd_path):
        edges = get_commits_edges()
        try:
            G = nx.DiGraph()
            for relation in edges:
                src_node = relation[0]
                dest_node = relation[1]
                G.add_edge(src_node, dest_node) 
            pos = nx.spring_layout(G)  # compute graph layout
            nx.draw(G, pos, node_size=3000)  # draw nodes and edges
            nx.draw_networkx_labels(G, pos)  # draw node labels/names
            labels = nx.get_edge_attributes(G, 'wit graph')
            nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
            plt.show()
        except Exception as err:
            log(err)
    else:
        log(f"Error - wit directory not found in -> {cwd_path}")


def change_references_file(name: str) -> None:
    head_id = get_head_id()
    try:
        with open(str(REFERENCES_PATH), 'r') as reference_file:
            references_file_lines = reference_file.readlines()
    except Exception as err:
        log(err)
    else:
        references_file_lines[2] = f"{name}={head_id}\n"
        try:
            with open(str(REFERENCES_PATH), 'w') as reference_file:
                reference_file.writelines(references_file_lines)
        except Exception as err:
            log(err)


def branch(name: str) -> None:
    cwd_path = Path.cwd().absolute()
    if is_wit_dir_in_path(cwd_path):
        change_references_file(name)
    else:
        log(f"Error - wit directory not found in -> {cwd_path}")


def get_branch_id() -> str:
    try:
        with open(str(REFERENCES_PATH), 'r') as reference_file:
            return reference_file.readlines()[2][reference_file.readlines()[2].find('=') + 1:-1]  # verify \n or not [7:-1]
    except Exception as err:
        log(err)


def get_parents(commit_id: str) -> list:
    parents = []
    parent_id = get_parent_id(commit_id)
    while parent_id != "None":
        parents.append(parent_id)
        parent_id = get_parent_id(parent_id)
    return parents


def get_changed_files(branch_id: str, common_parent_id: str) -> list:
    branch_path = IMAGES_PATH / branch_id
    common_parent_path = IMAGES_PATH / common_parent_id
    not_staged_files = []
    if Path(branch_path).exists():
        diff_files = filecmp.dircmp(str(branch_path), str(common_parent_path)).diff_files
        for diff_file in diff_files:
            if diff_file[0] != '.':
                not_staged_files.append(branch_path + diff_file)
    for root, dirs, _files in os.walk(str(branch_path)):
        for sub_dir in dirs:
            full_path = Path(root) / sub_dir
            full_path_common = get_relative_path_for_staging(full_path, str(branch_path), str(common_parent_path))
            if full_path_common.exists():
                diff_files = filecmp.dircmp(str(full_path), str(full_path_common)).diff_files
                for diff_file in diff_files:
                    if diff_file[0] != '.':
                        not_staged_files.append(str(full_path / diff_file))
    return not_staged_files


def move_changed_files_to_staging_area(changed_files_list: list, branch_id: str) -> None:
    for changed_file in changed_files_list:
        relative_path_in_staging_area = get_relative_path_for_staging(Path(changed_file), str(IMAGES_PATH / branch_id), str(STAGING_AREA_PATH))
        if relative_path_in_staging_area.exists():
            try:
                relative_path_in_staging_area.unlink()
            except Exception as err:
                log(err)
            else:
                try: 
                    shutil.copyfile(changed_file, str(relative_path_in_staging_area))
                except Exception as err:
                    log(err)     
        else:
            log(f"Error - couldn't find staging area file -> {relative_path_in_staging_area}")


def merge(beanch_name: str) -> None:
    cwd_path = Path.cwd().absolute()
    if is_wit_dir_in_path(cwd_path):
        head_id = get_head_id()
        branch_id = get_branch_id()
        head_parents = get_parents(head_id)
        branch_parents = get_parents(branch_id)
        for head_parent in head_parents:
            if head_parent in branch_parents:
                common_parent_id = head_parent
                break
        changed_files_list = get_changed_files(branch_id, common_parent_id)
        move_changed_files_to_staging_area(changed_files_list, branch_id)
        commit("automatic commit after merge", branch_id)
    else:
        log(f"Error - wit directory not found in -> {cwd_path}")


if __name__ == "__main__":
    argvs = sys.argv
    print(argvs)
    if len(argvs) == 2:
        if argvs[1] == "init":
            init()
        elif argvs[1] == "status":
            status()
        elif argvs[1] == "graph":
            graph()
    elif len(argvs) == 3:
        if argvs[1] == "add":
            add(argvs[2])  # The path to add
        elif argvs[1] == "commit":
            commit(argvs[2])  # The message
        elif argvs[1] == "checkout":
            checkout(argvs[2])  # Commit id / branch
        elif argvs[1] == "branch":
            branch(argvs[2])  # NAME
        elif argvs[1] == "merge":
            merge(argvs[2])  # branch name