while ($true) {
  try { & (Join-Path $PSScriptRoot "click-dialog.ps1") } catch { }
  Start-Sleep -Seconds 15
}
