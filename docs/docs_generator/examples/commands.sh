# This script generates CLI documentation in DOCX format for various Maestro3 components

#R8S Reference Guide
python "C:\Maestro3\m3-modular-admin\docs\docs_generator\src\generate_cli_docx.py" -f "C:\Maestro3\r8s\r8s\r8scli\group\r8s.py" -e r8s -o examples_v5f\r8s_reference_guide.docx --generate-md -dc "R8S-DOCS-100" -v "Version 1.0.0"
#SRE Reference Guide
python "C:\Maestro3\m3-modular-admin\docs\docs_generator\src\generate_cli_docx.py" -f "C:\Maestro3\test_ecc_cli\syndicate-rule-engine\cli\srecli\group\sre.py" -e sre -o examples_v5f\sre_reference_guide.docx --generate-md -dc "SRE-DOCS-100" -v "Version 1.0.0"
#SEP/STM Reference Guide
python "C:\Maestro3\m3-modular-admin\docs\docs_generator\src\generate_cli_docx.py" -f "C:\Maestro3\syndicate-education-platform\syndicate-task-manager\cli\stm\stm_group\stm.py" -e stm -o examples_v5f\stm_reference_guide.docx --generate-md -dc "STM-DOCS-100" -v "Version 1.0.0"
#SLM Reference Guide
python "C:\Maestro3\m3-modular-admin\docs\docs_generator\src\generate_cli_docx.py" -f "C:\Maestro3\custodian-as-a-service-license-manager\cli\slm\group\slm.py" -e slm -o examples_v5f\slm_reference_guide.docx --generate-md -dc "SLM-DOCS-100" -v "Version 1.0.0"
#m3admin Reference Guide
python "C:\Maestro3\m3-modular-admin\docs\docs_generator\src\generate_cli_docx.py" -f "C:\Maestro3\m3admin\src\m3_admin\group\m3admin.py" -e m3admin -o examples_v5f\m3admin_reference_guide.docx --generate-md -dc "M3Admin-DOCS-100" -v "Version 1.0.0"
