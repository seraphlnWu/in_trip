import tasks
wait_min = 60 
import rq 


if __name__ == "__main__":
    tasks.q_update.enqueue(tasks.update_all,wait_min)
    tasks.q_new.enqueue(tasks.get_new_url)
    tasks.q_retry.enqueue(tasks.retry)
    #tasks.update_worker.work()
    #tasks.new_worker.work()
    print "Start....."
