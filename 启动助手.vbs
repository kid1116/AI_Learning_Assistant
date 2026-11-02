Option Explicit
Dim files, shell, folder, python, script
Set files = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
folder = files.GetParentFolderName(WScript.ScriptFullName)
python = files.BuildPath(folder, "venv\Scripts\pythonw.exe")
script = files.BuildPath(folder, "desktop.py")
If Not files.FileExists(python) Then
    MsgBox "Python environment not found. Please follow README.md to create venv and install requirements.", 48, "AI Learning Assistant"
    WScript.Quit 1
End If
shell.CurrentDirectory = folder
shell.Run Chr(34) & python & Chr(34) & " " & Chr(34) & script & Chr(34), 0, False
