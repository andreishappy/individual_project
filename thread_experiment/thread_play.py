import thread

def print_number(lis):
    for elem in lis:
        print elem

if __name__ == "__main__":
    active_threads = []
    for i in range(0,3):
        active_threads.append(thread.start_new_thread(print_number, ([i,i,i,i,i,i,i],) ))

    for th in active_threads:
        th.join()
