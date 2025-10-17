from functions.run_python_file import run_python_file


def print_result(case_label, result):
    print(case_label)
    if isinstance(result, str) and result.startswith('Error:'):
        print('    ' + result)
    else:
        # Print first 400 chars so typical output is visible
        preview = result[:400]
        print('    ' + preview)
        if len(result) > 400:
            print('    ... (output truncated in test display)')
    print()


if __name__ == '__main__':
    # 1) run main.py with no args (should show usage)
    res = run_python_file('calculator', 'main.py')
    print_result('run_python_file("calculator", "main.py")', res)

    # 2) run main.py with calculator expression
    res = run_python_file('calculator', 'main.py', ['3 + 5'])
    print_result('run_python_file("calculator", "main.py", ["3 + 5"])', res)

    # 3) run calculator/tests.py
    res = run_python_file('calculator', 'tests.py')
    print_result('run_python_file("calculator", "tests.py")', res)

    # 4) attempt to run a file outside the working dir
    res = run_python_file('calculator', '../main.py')
    print_result('run_python_file("calculator", "../main.py")', res)

    # 5) non-existent file
    res = run_python_file('calculator', 'nonexistent.py')
    print_result('run_python_file("calculator", "nonexistent.py")', res)

    # 6) non-py file
    res = run_python_file('calculator', 'lorem.txt')
    print_result('run_python_file("calculator", "lorem.txt")', res)
