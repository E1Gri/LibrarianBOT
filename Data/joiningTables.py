import pandas as pd

file_list = [
    "Lite.csv",
    "Serious.csv"
]

cleaned_tables = []
all_genres = set()  

for file in file_list:
    try:
        df = pd.read_csv(file, sep=';', encoding='utf-8', dtype=str)
        df_clean = df.drop_duplicates()
        cleaned_tables.append(df_clean)
        print(f"Обработан файл: {file}")

    except Exception as e:
        print(f"Ошибка при обработке файла {file}: {e}")

if cleaned_tables:
    combined_table = pd.concat(cleaned_tables, ignore_index=True)
    combined_table = combined_table.drop_duplicates() # на всякий случай

    output_file = "Combined_clean_tables.csv"
    combined_table.to_csv(output_file, index=False, sep=';', encoding='utf-8')
    print(f"Объединённая таблица сохранена в: {output_file}")

    for genres_str in combined_table['genres'].dropna():
        genres_list = [genre.strip() for genre in genres_str.split(',')]
        all_genres.update(genres_list)

    if all_genres:
        with open('genres.txt', 'w', encoding='utf-8') as f:
            for genre in sorted(all_genres):
                f.write(genre + '\n')
        print(f"Уникальные жанры сохранены в файл genres.txt, всего их: {len(all_genres)}")
    else:
        print("Жанры не найдены ни в одном файле")
else:
    print("Ни один файл не был успешно обработан")