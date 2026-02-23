

# dump both genai and generativeai information
import traceback
with open('module_info.txt','w', encoding='utf-8') as f:
    try:
        import google.generativeai as gai
        f.write('generativeai file: '+getattr(gai,'__file__','<none>')+'\n')
        f.write('generativeai version: '+str(getattr(gai,'__version__',None))+'\n')
        f.write('generativeai attrs: '+', '.join([a for a in dir(gai) if not a.startswith('_')])+'\n')
    except Exception as e:
        f.write('generativeai import failed: '+traceback.format_exc()+'\n')
    try:
        import google.genai as gi
        f.write('genai file: '+getattr(gi,'__file__','<none>')+'\n')
        f.write('genai version: '+str(getattr(gi,'__version__',None))+'\n')
        f.write('genai attrs: '+', '.join([a for a in dir(gi) if not a.startswith('_')])+'\n')
    except Exception as e:
        f.write('genai import failed: '+traceback.format_exc()+'\n')
