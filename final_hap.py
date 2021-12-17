##The script calculates the similarity ratio using the Levenshtein
#distance between the item names from HAP and the result of the comparison of SUEP and POP.

import pandas as pd
from tqdm import tqdm
import numpy as np
from fuzzywuzzy import fuzz, process
import os

#Import data
hap_test_file = pd.ExcelFile("Datensatztabelle_NUM2_Rel_11_20210720-171302.xlsx")
final_test_file = pd.ExcelFile("20210914_final_SUEP.xlsx")

#Data preparation
hap_list = []
final_list = []

hap_names = hap_test_file.sheet_names[2:]
final_names = final_test_file.sheet_names[:]

for sheet in hap_names:
    sheet = pd.read_excel(hap_test_file,
                          sheet_name=sheet,
                          na_values="<->")
    start_index = np.where(sheet["Projekt"] == "Nr.")[0][0]
    sheet.columns = sheet.iloc[start_index]
    sheet = sheet.iloc[(start_index) + 1:, :].reset_index(drop=True)
    sheet.dropna(subset=["Item"], inplace=True)  # DROP
    hap_list.append(sheet)


for sheet in suep_names:
    sheet = pd.read_excel(final_test_file,
                          sheet_name=sheet,
                          na_values="<->")
    sheet = sheet.iloc[(start_index) + 1:, :].reset_index(drop=True)
    sheet["Item"] = sheet["Item"]
    sheet["Datenbankspalte"] = sheet["Datenbankspalte"]
    print(sheet)
    suep_list.append(sheet)


#Vectorized calculation of the similarity ratio

def vect_fuzz(x, y):
    return fuzz.token_sort_ratio(x, y)


vect = np.vectorize(vect_fuzz)


output = pd.DataFrame()
ls1 = []
for hap_sheet in tqdm(range(len(hap_list))):
    if not all(hap_list[hap_sheet]["Item"].isnull()):
        df1 = hap_list[hap_sheet]
        df1.dropna(subset=["Datenbankspalte"], inplace=True)  # DROP
        df1["dummy"] = True
        df1["Sheet_name"] = hap_names[hap_sheet]
    for final_sheet in range(len(final_list)):
        if not all(final_list[final_sheet]["Item"].isnull()):
            df2 = final_list[final_sheet]
            df2.dropna(subset=["Datenbankspalte"], inplace=True)  # DROP
            df2["dummy"] = True
            df2["Sheet_name"] = df2["Sheet_name"]
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
output2.to_csv(os.path.join("Output", f"final&hap_"+ratiostr+".csv"),
                  index=False)



