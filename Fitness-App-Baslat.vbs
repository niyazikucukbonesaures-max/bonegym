' ========================================
' Fitness Kalori Takip Uygulaması
' Optimize Edilmiş Başlatma Scripti
' ========================================

Option Explicit

Dim WshShell, fso, currentDir, backendPath, frontendPath
Dim backendCmd, frontendCmd, browserUrl

' Shell ve FileSystemObject oluştur
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Mevcut dizini al
currentDir = WshShell.CurrentDirectory

' Backend ve Frontend yollarını kontrol et
backendPath = currentDir & "\backend"
frontendPath = currentDir & "\frontend"

' Yolların varlığını kontrol et
If Not fso.FolderExists(backendPath) Then
    MsgBox "HATA: Backend klasörü bulunamadı!" & vbCrLf & "Yol: " & backendPath, vbCritical, "Fitness App"
    WScript.Quit
End If

If Not fso.FolderExists(frontendPath) Then
    MsgBox "HATA: Frontend klasörü bulunamadı!" & vbCrLf & "Yol: " & frontendPath, vbCritical, "Fitness App"
    WScript.Quit
End If

' Python kontrolü
On Error Resume Next
WshShell.Run "python --version", 0, True
If Err.Number <> 0 Then
    MsgBox "HATA: Python yüklü değil!" & vbCrLf & "Lütfen Python'u yükleyin.", vbCritical, "Fitness App"
    WScript.Quit
End If
On Error GoTo 0

' Node.js kontrolü
On Error Resume Next
WshShell.Run "node --version", 0, True
If Err.Number <> 0 Then
    MsgBox "HATA: Node.js yüklü değil!" & vbCrLf & "Lütfen Node.js'i yükleyin.", vbCritical, "Fitness App"
    WScript.Quit
End If
On Error GoTo 0

' Bilgilendirme mesajı
MsgBox "Fitness Kalori Takip Uygulaması başlatılıyor..." & vbCrLf & vbCrLf & _
       "✓ Backend: http://localhost:8000" & vbCrLf & _
       "✓ Frontend: http://localhost:5173" & vbCrLf & vbCrLf & _
       "Tarayıcınız otomatik açılacak.", vbInformation, "Fitness App"

' Backend komutunu oluştur ve çalıştır
backendCmd = "cmd /c ""cd /d " & backendPath & " && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"""
WshShell.Run backendCmd, 1, False

' Backend'in başlaması için bekle (5 saniye)
WScript.Sleep 5000

' Frontend komutunu oluştur ve çalıştır
frontendCmd = "cmd /c ""cd /d " & frontendPath & " && npm run dev"""
WshShell.Run frontendCmd, 1, False

' Frontend'in başlaması için bekle (5 saniye)
WScript.Sleep 5000

' Tarayıcıyı aç
browserUrl = "http://localhost:5173"
WshShell.Run browserUrl, 1

' Başarı mesajı
MsgBox "✓ Uygulama başarıyla başlatıldı!" & vbCrLf & vbCrLf & _
       "Tarayıcınızda açıldı: " & browserUrl & vbCrLf & vbCrLf & _
       "Kapatmak için: Fitness-App-Durdur.vbs", vbInformation, "Fitness App"

' Temizlik
Set fso = Nothing
Set WshShell = Nothing
