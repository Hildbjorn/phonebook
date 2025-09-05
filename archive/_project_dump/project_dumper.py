import os

def create_project_dump(root_dir, output_file, exclude_dirs=None):
    # Добавляем исключаемые папки static и staticfiles
    if exclude_dirs is None:
        exclude_dirs = ['.idea', '.vscode', '', 'env','venv', '.git',
                        '__pycache__', 'node_modules', 'media', 'static', 'staticfiles']

    with open(output_file, 'w', encoding='utf-8') as outfile:
        first_file = True

        for root, dirs, files in os.walk(root_dir):
            # Исключаем ненужные директории
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                # Пропускаем manage.py и SQLite файлы
                if file == 'manage.py' or file.endswith('.sqlite3'):
                    continue

                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, root_dir)

                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                except UnicodeDecodeError:
                    content = f"!!! Файл содержит бинарные данные и не может быть прочитан !!!"
                except Exception as e:
                    content = f"!!! Ошибка при чтении файла: {str(e)} !!!"

                if not first_file:
                    outfile.write("\n\n-----\n\n")

                # Заголовок файла в формате Markdown
                outfile.write(f"# Файл: {relative_path}\n\n")
                # Обрамляем содержимое файла в тройные кавычки
                outfile.write("```\n")
                outfile.write(content)
                outfile.write("\n```\n")
                first_file = False

if __name__ == "__main__":
    project_root = input("Введите путь к корневой директории проекта: ")
    output_filename = "project_dump.md"  # Изменяем расширение на .md

    create_project_dump(project_root, output_filename)
    print(f"Дамп проекта создан в файле: {output_filename}")