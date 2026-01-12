
import re

def check_template_balance(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    stack = []
    
    # Regex for tags
    # We care about: if, for, block, with, while (custom?), lifecycle
    # And their ends: endif, endfor, endblock, endwith
    # And intermediates: else, elif, empty
    
    tag_re = re.compile(r'{%\s*(\w+).*?%}')
    
    # helper
    def is_start_tag(tag):
        return tag in ['if', 'for', 'block', 'with', 'autoescape', 'comment']
        
    def is_end_tag(tag):
        return tag.startswith('end')
        
    def get_end_for_start(tag):
        return 'end' + tag

    with open('debug_log.txt', 'w', encoding='utf-8') as log:
        def log_print(msg):
            print(msg)
            log.write(msg + '\n')
            
        log_print(f"Checking {filepath}...")
        
        for i, line in enumerate(lines):
            line_num = i + 1
            matches = tag_re.finditer(line)
            for match in matches:
                content = match.group(1)
                
                if is_start_tag(content):
                    stack.append((content, line_num))
                    log_print(f"{line_num}: Push {content} -> Stack: {[x[0] for x in stack]}")
                
                elif is_end_tag(content):
                    if not stack:
                        log_print(f"ERROR: Found {content} at {line_num} but stack is empty!")
                        return
                    
                    last_tag, last_line = stack[-1]
                    expected_end = get_end_for_start(last_tag)
                    
                    if content == expected_end:
                        stack.pop()
                        log_print(f"{line_num}: Pop {content} (matched {last_tag} from {last_line}) -> Stack: {[x[0] for x in stack]}")
                    else:
                        log_print(f"ERROR: Found {content} at {line_num} but expected {expected_end} (for {last_tag} at {last_line})")
                        return

                elif content in ['else', 'elif', 'empty']:
                    if not stack:
                        log_print(f"ERROR: Found {content} at {line_num} but stack is empty!")
                        return
                    parent = stack[-1][0]
                    # if parent not in ['if', 'for', 'changed']:
                    #    log_print(f"WARNING: Found {content} at {line_num} inside {parent}?")
                    log_print(f"{line_num}: Saw {content} inside {parent}")

        if stack:
            log_print(f"ERROR: Unclosed tags at EOF: {stack}")
        else:
            log_print("SUCCESS: Template structure seems balanced.")

if __name__ == "__main__":
    check_template_balance(r"c:\Users\vagne\OneDrive\Desktop\sicfaae\templates\candidaturas\lista_candidatos.html")
