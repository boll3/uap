#!/usr/bin/env python

import sys
import copy
import logging
import os
import signal
import socket
import yaml

from .. import misc
from .. import pipeline
from .. import process_pool

logger = logging.getLogger("uap_logger")

def main(args):
    p = pipeline.Pipeline(arguments=args)
    def handle_signal(signum, frame):
        print("Catching %s!" % process_pool.ProcessPool.SIGNAL_NAMES[signum])
        p.caught_signal = signum
        process_pool.ProcessPool.kill()
        
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    #embed()
    
    #task_list = copy.deepcopy(p.all_tasks_topologically_sorted)
    task_list = p.all_tasks_topologically_sorted

    if len(args.step_task) >= 1:
        # execute the specified tasks
        task_list = list()
        for task_id in args.step_task:
            if '/' in task_id:
                task = p.task_for_task_id[task_id]
                task_list.append(task)
            else:
                for task in p.all_tasks_topologically_sorted:
                    if str(task)[0:len(task_id)] == task_id:
                        task_list.append(task)
            
    # execute all tasks
    for task in task_list:
        basic_task_state = task.get_task_state_basic()
        if basic_task_state == p.states.FINISHED:
            sys.stderr.write("Skipping %s because it's already finished.\n" % task)
            continue
        if basic_task_state == p.states.READY:
            task.run()
        else:
            raise Exception("Unexpected basic task state for %s: %s" % (task, basic_task_state))

if __name__ == '__main__':
    try:
        main()
    finally:
        # make sure all child processes get terminated
        process_pool.ProcessPool.kill_all_child_processes()