# Close Revit's 'Virtual Memory - High Usage' TaskDialog (and any #32770 whose only sensible button is Close). Interactive session only.
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System; using System.Runtime.InteropServices;
public class WM { [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr h); }
"@
$log = (Join-Path $PSScriptRoot "click-dialog.log")
"=== $(Get-Date) ===" | Out-File -Encoding utf8 -Append $log
$root = [System.Windows.Automation.AutomationElement]::RootElement
$revitPid = (Get-Process Revit -ErrorAction SilentlyContinue).Id
$pidCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ProcessIdProperty, [int]$revitPid)
$winCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Window)
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.AndCondition($pidCond, $winCond)))
foreach ($w in $wins) {
  if ($w.Current.ClassName -ne "#32770") { continue }
  $name = $w.Current.Name; $h = [IntPtr]$w.Current.NativeWindowHandle
  "dialog: '$name' hwnd=$h" | Out-File -Encoding utf8 -Append $log
  $all = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
  $i = 0; foreach ($e in $all) { $i++; if ($i -le 25) { "  child: $($e.Current.ControlType.ProgrammaticName) [$($e.Current.ClassName)] '$($e.Current.Name)'" | Out-File -Encoding utf8 -Append $log } }
  if ($name -notmatch "Virtual Memory") { "  not the memory dialog; leaving it" | Out-File -Encoding utf8 -Append $log; continue }
  # 0) tick "Do not show me this message again" so the session stops raising it
  foreach ($e in $all) { if ($e.Current.ControlType -eq [System.Windows.Automation.ControlType]::CheckBox) { try { $tp = $e.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern); if ($tp.Current.ToggleState -ne [System.Windows.Automation.ToggleState]::On) { $tp.Toggle(); "  ticked '$($e.Current.Name)'" | Out-File -Encoding utf8 -Append $log } } catch { "  checkbox toggle failed: $($_.Exception.Message)" | Out-File -Encoding utf8 -Append $log } } }
  # 1) any element named Close with an Invoke pattern
  $closeEl = $null
  foreach ($e in $all) { if ($e.Current.Name -eq "Close") { $closeEl = $e; break } }
  if ($closeEl) { try { $closeEl.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke(); "  invoked Close element" | Out-File -Encoding utf8 -Append $log } catch { "  Close element has no Invoke: $($_.Exception.Message)" | Out-File -Encoding utf8 -Append $log } }
  Start-Sleep -Milliseconds 800
  if ([WM]::IsWindow($h)) { [WM]::PostMessage($h, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null; "  posted WM_CLOSE" | Out-File -Encoding utf8 -Append $log; Start-Sleep -Milliseconds 800 }
  if ([WM]::IsWindow($h)) { [WM]::SetForegroundWindow($h) | Out-Null; Start-Sleep -Milliseconds 300; [System.Windows.Forms.SendKeys]::SendWait("{ENTER}"); "  sent ENTER" | Out-File -Encoding utf8 -Append $log; Start-Sleep -Milliseconds 800 }
  "  dialog still present: $([WM]::IsWindow($h))" | Out-File -Encoding utf8 -Append $log
}
"done" | Out-File -Encoding utf8 -Append $log
