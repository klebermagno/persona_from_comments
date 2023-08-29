import sys

from gathering import Gathering
from mining import Mining
from analysis import Analysis
from generating import Generating


def main(video_id):
    gathering = Gathering()
    gathering.execute(video_id)
    mining = Mining()
    mining.execute(video_id)
    analysis = Analysis()
    analysis.execute(video_id)
    generating = Generating()
    generating.execute(video_id)
    
if __name__ == '__main__':
    video_id = str(sys.argv[1])
    
    main(video_id)
    
    
    