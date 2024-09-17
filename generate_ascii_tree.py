def generate_ascii_tree(input_text):
    lines = input_text.strip().split('\n')
    tree = {}
    current_path = []
    
    for line in lines:
        indent = (len(line) - len(line.lstrip()))/2
        name = line.strip()
        
        while len(current_path) > indent:
            current_path.pop()
        
        if indent == len(current_path):
            current_path.append(name)
        
        current = tree
        for path in current_path:
            if path not in current:
                current[path] = {}
            current = current[path]

    print(tree)
    
    def print_tree(node, prefix="", is_last=True):
        output = []
        keys = list(node.keys())
        
        for i, key in enumerate(keys):
            is_last_item = i == len(keys) - 1
            new_prefix = prefix + ("    " if is_last_item else "│   ")
            output.append(f"{prefix}{'└── ' if is_last_item else '├── '}{key}{'/' if node[key] else ''}")
            
            if node[key]:
                output.extend(print_tree(node[key], new_prefix, is_last_item))
        
        return output

    result = ["."] + print_tree(tree)
    return "\n".join(result)

# Example usage
input_text = """
files
archiveinfo
  users
    Eskil2
      messages
        Eskil2
          a-6RpYbE1kP0rlmkmfxQNTElbop0rveA.acs
        Eskil
          SUHSHGigw9ACvZ0UxYqDx4umJ3zFf7-7.acs
      public.asc
    Eskil
      messages
        Eskil2
          ycQckzNr6yKnNzx16znrYjxJkUflmQ9y.acs
      public.asc
"""

print(generate_ascii_tree(input_text))