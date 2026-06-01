' ========================================
' Fitness Kalori Takip Uygulaması
' Optimize Edilmiş Durdurma Scripti
' ========================================

Option Explicit

Dim WshShell, objWMI, colProcesses, objProcess
Dim backendKilled, frontendKilled, totalKilled

' Shell oluştur
Set WshShell = CreateObject("WScript.Shell")
Set objWMI = GetObject("winmgmts:\\.\root\cimv2")

backendKilled = 0
frontendKilled = 0
totalKilled = 0

' Onay mesajı
Dim result
result = MsgBox("Fitness Kalori Takip Uygulamasını kapatmak istediğinize emin misiniz?" & vbCrLf & vbCrLf & _
                "✓ Backend sunucusu kapatılacak" & vbCrLf & _
                "✓ Frontend sunucusu kapatılacak", vbQuestion + vbYesNo, "Fitness App")

If result = vbNo Then
    WScript.Quit
End If

' Python/Uvicorn process'lerini bul ve kapat
Set colProcesses = objWMI.ExecQuery("SELECT * FROM Win32_Process WHERE Name = 'python.exe'")
For Each objProcess In colProcesses
    If InStr(objProcess.CommandLine, "uvicorn") > 0 Then
        objProcess.Terminate()
        backendKilled = backendKilled + 1
        totalKilled = totalKilled + 1
    End If
Next

' Node.js/Vite process'lerini bul ve kapat
Set colProcesses = objWMI.ExecQuery("SELECT * FROM Win32_Process WHERE Name = 'node.exe'")
For Each objProcess In colProcesses
    If InStr(objProcess.CommandLine, "vite") > 0 Or InStr(objProcess.CommandLine, "npm") > 0 Then
        objProcess.Terminate()
        frontendKilled = frontendKilled + 1
        totalKilled = totalKilled + 1
    End If
Next

' CMD pencerelerini kapat
WshShell.Run "taskkill /F /FI ""WINDOWTITLE eq Backend Server*"" >nul 2>&1", 0, True
WshShell.Run "taskkill /F /FI ""WINDOWTITLE eq Frontend Server*"" >nul 2>&1", 0, True

' Kısa bekleme
WScript.Sleep 1000

' Sonuç mesajı
If totalKilled > 0 Then
    MsgBox "✓ Uygulama başarıyla kapatıldı!" & vbCrLf & vbCrLf & _
           "Backend: " & backendKilled & " process kapatıldı" & vbCrLf & _
           "Frontend: " & frontendKilled & " process kapatıldı" & vbCrLf & vbCrLf & _
           "Toplam: " & totalKilled & " process", vbInformation, "Fitness App"
Else
    MsgBox "⚠ Çalışan uygulama bulunamadı!" & vbCrLf & vbCrLf & _
           "Uygulama zaten kapalı olabilir.", vbExclamation, "Fitness App"
End If

' Temizlik
Set colProcesses = Nothing
Set objWMI = Nothing
Set WshShell = Nothing
