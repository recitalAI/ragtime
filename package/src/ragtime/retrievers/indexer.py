import os
import hashlib
import pickle
import shutil
from pathlib import Path
from ragtime.config import DATASETS_FOLDER_NAME, DOCUMENTS_FOLDER_NAME
from ragtime.expe import Expe
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    SimpleDirectoryReader,
    load_index_from_storage,
)


class Indexer:
    def __init__(self, name, base_dir=DATASETS_FOLDER_NAME):
        self.name = name
        self.base_dir = base_dir
        self.storage_path = os.path.join(base_dir, name, "storage")

    def list_files(self):
        files_list = []
        for root, dirs, files in os.walk(os.path.join(self.base_dir, self.name)):
            if os.path.basename(root) == DOCUMENTS_FOLDER_NAME:
                for file in files:
                    file_path = os.path.join(root, file)
                    if not file.startswith("."):
                        files_list.append(file_path)
        if len(files_list) > 50:
            raise Exception("La liste des fichiers dépasse la limite de 50 fichiers.")
        return files_list

    def read_doc(self, recursive=True):
        return SimpleDirectoryReader(
            input_files=self.list_files(), exclude_hidden=False, recursive=recursive
        ).load_data()

    def generate_hash(self):
        files_list = self.list_files()
        concatenated_names = "".join(
            [os.path.basename(file_path) for file_path in files_list]
        )
        unique_hash = hashlib.md5(concatenated_names.encode()).hexdigest()
        return unique_hash

    def find_dir_with_hash(self, hash_value):
        if not os.path.exists(self.storage_path):
            return None
        for dir_name in os.listdir(self.storage_path):
            dir_path = os.path.join(self.storage_path, dir_name)
            if os.path.isdir(dir_path):
                hash_file = os.path.join(dir_path, "hash.txt")
                if os.path.exists(hash_file):
                    with open(hash_file, "r") as f:
                        existing_hash = f.read()
                    if existing_hash == hash_value:
                        return dir_path
        return None

    def create_storage_directory(self, dir_index=True):
        storage_dir = os.path.join(self.storage_path)

        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)

        hash_dir = os.path.join(storage_dir, "hashes")
        os.makedirs(hash_dir, exist_ok=True)
        nodes_dir = os.path.join(storage_dir, "nodes")
        os.makedirs(nodes_dir, exist_ok=True)

        if dir_index:
            main_dir = os.path.join(storage_dir, f"Index_storage_{self.name}")
            os.makedirs(main_dir, exist_ok=True)
            return main_dir, hash_dir, nodes_dir
        else:
            return None, hash_dir, nodes_dir

    def save_hash(self, unique_hash, hash_dir):
        hash_file_path = os.path.join(hash_dir, "hash.txt")

        if os.path.exists(hash_dir):
            try:
                with open(hash_file_path, "w") as hash_file:
                    hash_file.write(unique_hash)
                return True
            except Exception as e:
                print(
                    f"Une erreur s'est produite lors de l'enregistrement du hachage : {e}"
                )
                return False
        else:
            print(
                f"Le répertoire '{hash_dir}' n'existe pas. Impossible d'enregistrer le hachage."
            )
            return False

    def create_or_load_nodes(
        self, recursive=True, check_existance=True, create_index=True
    ):
        new_hash = self.generate_hash()
        existing_dir = self.find_dir_with_hash(new_hash)

        if check_existance and existing_dir:
            nodes_file = os.path.join(self.storage_path, "nodes", "nodes.pkl")
            with open(nodes_file, "rb") as f:
                nodes = pickle.load(f)

            if create_index:
                index_file = os.path.join(
                    self.storage_path, f"Index_storage_{self.name}"
                )
                if not os.path.exists(index_file):
                    os.makedirs(index_file, exist_ok=True)
                if os.path.exists(index_file) and not os.listdir(index_file):
                    storage_context = StorageContext.from_defaults()
                    storage_context.docstore.add_documents(nodes)
                    index = VectorStoreIndex(nodes, storage_context=storage_context)
                    index.storage_context.persist(persist_dir=index_file)
                else:
                    storage_context = StorageContext.from_defaults(
                        persist_dir=index_file
                    )
                    index = load_index_from_storage(storage_context)
                return nodes, index
            else:
                return nodes, None

        if os.path.exists(self.storage_path):
            shutil.rmtree(self.storage_path)

        documents = self.read_doc(recursive=recursive)
        splitter = SentenceSplitter(chunk_size=2048)
        nodes = splitter.get_nodes_from_documents(documents)

        main_dir, hash_dir, nodes_dir = self.create_storage_directory(
            dir_index=create_index
        )

        self.save_hash(new_hash, hash_dir)
        nodes_file = os.path.join(nodes_dir, "nodes.pkl")
        with open(nodes_file, "wb") as f:
            pickle.dump(nodes, f)

        if create_index:
            storage_context = StorageContext.from_defaults()
            storage_context.docstore.add_documents(nodes)
            index = VectorStoreIndex(nodes, storage_context=storage_context)
            index.storage_context.persist(persist_dir=main_dir)
            return nodes, index
        else:
            return nodes, None


def annotation_human_auto(path: Path):
    # Charger la structure JSON depuis un fichier
    expe: Expe = Expe(json_path=path)

    for idx, item in enumerate(expe.items):
        for answer in item.answers.items:
            human_eval = answer.eval.human
            if human_eval != 1:
                answer.eval.human = 1
    expe.save_to_json(path=path)
    return expe
