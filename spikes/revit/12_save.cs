doc.Save();
int n = 0; foreach (Document d in uiapp.Application.Documents) n++;
return "saved " + doc.PathName + " | modified=" + doc.IsModified + " | active=" + uiapp.ActiveUIDocument.Document.Title + " | open docs=" + n;
