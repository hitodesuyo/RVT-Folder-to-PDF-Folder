import clr
import os

## REVIT API PART
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import (FilteredElementCollector, ViewSheet, PDFExportOptions, ModelPathUtils, OpenOptions, ElementId)

## DYNAMO/REVIT CONNECTION
clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

## .NET LIST
clr.AddReference("System")
from System.Collections.Generic import List

uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application

# IN[0] = folder containing .RVT files
# IN[1] = folder where .PDF files should go
source_folder = IN[0]
output_folder = IN[1]

results = []

def clean_filename(name):
    invalid_chars = '<>"/\\|?*'
    for char in invalid_chars: name = name.replace(char, "_")
    return name.strip()

## FIND ALL .RVT FILES
rvt_files = [
    os.path.join(source_folder, f)
    for f in os.listdir(source_folder) if f.lower().endswith(".rvt")]

rvt_files.sort()

for rvt_path in rvt_files:
    doc = None
    try:
        # OPEN RVT
        model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(rvt_path)
        options = OpenOptions()
        
        doc = app.OpenDocumentFile(model_path, options)
        
        # FIND PRINTABLE SHEETS
        sheets = [s for s in FilteredElementCollector(doc).OfClass(ViewSheet) if not s.IsPlaceholder and s.CanBePrinted]
        
        if len(sheets) == 0:
            results.append("SKIPPED - No printable sheet: " + os.path.basename(rvt_path))
            doc.Close(False)
            continue
        
        # USE FIRST SHEET
        sheets.sort(key=lambda x: x.SheetNumber)
        sheet = sheets[0]
        
        # CREATE LIST CONTAINING SHEET ID
        sheet_ids = List[ElementId]()
        sheet_ids.Add(sheet.Id)
        
        # PDF OPTIONS
        pdf_options = PDFExportOptions()
        pdf_options.Combine = True
        pdf_options.StopOnError = True
        
        # FORCE RASTER FOR PROBLEM FILES
        pdf_options.AlwaysUseRaster = True
        pdf_options.RasterQuality = 600
        pdf_options.MaskCoincidentLines = True
        
        # NAME PDF AFTER RVT FILE
        base_name = os.path.splitext(os.path.basename(rvt_path))[0]
        
        base_name = clean_filename(base_name)
        
        pdf_options.FileName = base_name
        
        # EXPORT PDF
        success = doc.Export(output_folder, sheet_ids, pdf_options)
        
        if success: results.append("EXPORTED - " + base_name + ".pdf")
        else: results.append("FAILED - " + os.path.basename(rvt_path))
        
        # CLOSE FILE WITHOUT SAVING
        doc.Close(False)
        
    except Exception as error:
        results.append("ERROR - {} {}".format(os.path.basename(rvt_path), str(error)))
        
        if doc is not None:
            try: doc.Close(False)
            except: pass

OUT = results
