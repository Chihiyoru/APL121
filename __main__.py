import os
import shutil
import random
import string
import customtkinter

from main_module import TestCase, SeminarWorkTester, FprgToPythonConverter;

from tkinter import *;
from tkinter import filedialog, messagebox

import tkinter as tk

from PIL import ImageTk, Image

FileTypes = [
    ('FPRG files', '.fprg'),  # or ('FPRG files', '*.fprg .FPRG')
    ('All files', '*.*')
]

if __name__ == "__main__":
    # #//DEBUG
    # test_cases = [
    #     TestCase(
    #         inputs=["6"],  # Testing factorial of 5
    #         expected_output="720\n",  # 5! = 120
    #         description="factorial_of_6"
    #     ),
    # ]

    # #// Create the tester
    # tester = SeminarWorkTester(FprgToPythonConverter())

    # #// Test a submission
    # results = tester.test_submission(os.path.join("Debug", "student_program.fprg"), test_cases)

    # #// Print the results
    # print(tester.generate_report(results))

    #//UI
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")

    app = customtkinter.CTk()

    app.title("Flogorithm")
    app.geometry("480x300")

    frame = customtkinter.CTkLabel(app,text="")
    frame.grid(row=0,column=0,sticky="w",padx=50,pady=20)



    def RequestFile():
        
        global FileName

        FileName = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select Flowgorithm file.",
            filetypes=FileTypes,
        )
        PathEntry.insert(0,FileName)
    
    def SubmitFile():

        SplitFileName = FileName.split(".")

        RandomText = ''.join((random.choice(string.ascii_lowercase) for x in range(12)))
        shutil.copy(FileName, f"./Temp/{RandomText}.{SplitFileName[1]}")

        test_cases = [
            TestCase(
                inputs=["6"],  # Testing factorial of 5
                expected_output="720\n",  # 5! = 120
                description="factorial_of_6"
            ),
            TestCase(
                inputs=["2"],  # Testing factorial of 5
                expected_output="2\n",  # 5! = 120
                description="factorial_of_6"
            ),
                TestCase(
                inputs=["4"],  # Testing factorial of 4
                expected_output="720\n",  # 4! = 24
                description="factorial_of_6"
            )
        ]

        #// Create the tester
        tester = SeminarWorkTester(FprgToPythonConverter())

        #// Test a submission
        results = tester.test_submission(os.path.join("Debug", "student_program.fprg"), test_cases)

        #CLEARING
        os.remove(os.path.join(os.getcwd(), "Temp", f"{RandomText}.{SplitFileName[1]}"))

        #// Print the results
        # print(tester.generate_report(results))
        messagebox.showinfo("Success", tester.generate_report(results))




    SelectButton = customtkinter.CTkButton(frame, text="Browse File", width=50,command=RequestFile)
    SaveButton = customtkinter.CTkButton(frame, text="Upload",width=50,command=SubmitFile)

    PathEntry = customtkinter.CTkEntry(frame, width=200)


    SelectButton.grid(row=0,column=0,padx=1,pady=5,ipady=0,sticky="e")
    SaveButton.grid(row=0,column=2,padx=1,pady=5,ipady=0,sticky="e")

    PathEntry.grid(row=0,column=1,padx=1,pady=5,ipady=0,sticky="e")



    app.resizable(False, False)
    app.mainloop()