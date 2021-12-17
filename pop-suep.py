#The script calculates the similarity ratio using the Levenshtein
#distance between the item names from SUEP and POP.

import pandas as pd
from tqdm import tqdm
import numpy as np
from fuzzywuzzy import fuzz, process
import os

#Import data
pop_test_file = pd.ExcelFile("Datensatztabelle_POP_V4_20210802.xlsx")
suep_test_file = pd.ExcelFile("Datensatztabelle_SUEP_20210802.xlsx")


#Data preparation
pop_list = []
suep_list = []

pop_names = pop_test_file.sheet_names[2:]
suep_names = suep_test_file.sheet_names[2:]


for sheet in pop_names:
    sheet = pd.read_excel(pop_test_file,
                          sheet_name=sheet,
                          na_values="<->")
    start_index = np.where(sheet["Projekt"] == "Nr.")[0][0]
    sheet.columns = sheet.iloc[start_index]
    sheet = sheet.iloc[(start_index) + 1:, :].reset_index(drop=True)
    sheet.dropna(subset=["Item"], inplace=True)  # DROP
    pop_list.append(sheet)


for sheet in suep_names:
    sheet = pd.read_excel(suep_test_file,
                          sheet_name=sheet,
                          na_values="<->")
    start_index = np.where(sheet["Projekt"] == "Nr.")[0][0]
    sheet.columns = sheet.iloc[start_index]
    sheet = sheet.iloc[(start_index) + 1:, :].reset_index(drop=True)
    sheet.dropna(subset=["Item"], inplace=True)  # DROP
    suep_list.append(sheet)

#Vectorized calculation of the similarity ratio

def vect_fuzz(x, y):
    return fuzz.token_sort_ratio(x, y)


vect = np.vectorize(vect_fuzz)


output = pd.DataFrame()
ls1 = []
for pop_sheet in tqdm(range(len(pop_list))):
    if not all(pop_list[pop_sheet]["Item"].isnull()):
        df1 = pop_list[pop_sheet]
        df1.dropna(subset=["Datenbankspalte"], inplace=True)  # DROP
        df1["dummy"] = True
        df1["Sheet_name"] = pop_names[pop_sheet]
    for suep_sheet in range(len(suep_list)):
        if not all(suep_list[suep_sheet]["Item"].isnull()):
            df2 = suep_list[suep_sheet]
            df2.dropna(subset=["Datenbankspalte"], inplace=True)  # DROP
            df2["dummy"] = True
            df2["Sheet_name"] = suep_names[suep_sheet]
            df = pd.merge(df1[["Item", "Datenbankspalte", "Sheet_name", "dummy"]],
                          df2[["Item", "Datenbankspalte", "Sheet_name", "dummy"]], on='dummy')
            df.drop('dummy', axis=1, inplace=True)
            ls1.append(df)



#Create the CSV with the result and a defined ratio
ratio = 40

output = pd.concat(ls1)
output['Token_Sort_Ratio'] = vect(output["Item_x"], output["Item_y"])
output2 = output[output['Token_Sort_Ratio'] >= ratio]
ratiostr= str(ratio)
output2 = output2.sort_values(by='Token_Sort_Ratio', ascending=False)
output2.to_csv(os.path.join("Output", f"pop_suep_"+ratiostr+".csv"),
                  index=False)

