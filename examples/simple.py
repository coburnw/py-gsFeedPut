import gs_feedput as gs
import simple_streams as fs

class ProjectConfig():
    project_id = 'simple' # corresponds to an entry in ~/.netrc
    sample_period_seconds = 10
    
    
class Frame1(gs.Component):
    def __init__(self):
        frame_id = 'frame_1'
        template = None # 'simple_template'
        super().__init__(frame_id, template)

        self.set_name('Frame One')
        self.set_description('Simple Frame')

        self.streams.append(fs.IpaStream('ipa', frame_id))

        return

    
if __name__ == '__main__':
    import time

    project = ProjectConfig()
    
    feed = gs.Feed(project.project_id, compress=True)
    frames = gs.Components(project.project_id)
    
    frame = Frame1()
    frames.append(frame)

    last_upload = time.time() - project.sample_period_seconds
    while True:
        frames.update()
        
        if (time.time() - last_upload) > project.sample_period_seconds:
            feed.put(frames)
            last_upload += project.sample_period_seconds

        time.sleep(1)
         
    # quit
    exit(0)
