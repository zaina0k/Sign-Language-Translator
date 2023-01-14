import audiomath; audiomath.RequireAudiomathVersion( '1.12.0' )
import speech_recognition 

class DuckTypedMicrophone( speech_recognition.AudioSource ): 
    # descent from AudioSource is required purely to pass an assertion in Recognizer.listen()
    def __init__( self, device=None, chunkSeconds=1024/44100.0 ):  
        # 1024 samples at 44100 Hz is about 23 ms
        self.recorder = None
        self.device = device
        self.chunkSeconds = chunkSeconds
    def __enter__( self ):
        self.nSamplesRead = 0
        self.recorder = audiomath.Recorder( audiomath.Sound( 5, nChannels=1 ), loop=True, device=self.device )
        # Attributes required by Recognizer.listen():
        self.CHUNK = audiomath.SecondsToSamples( self.chunkSeconds, self.recorder.fs, int )
        self.SAMPLE_RATE = int( self.recorder.fs )
        self.SAMPLE_WIDTH = self.recorder.sound.nbytes
        return self
    def __exit__( self, *blx ):
        self.recorder.Stop()
        self.recorder = None
    def read( self, nSamples ):
        sampleArray = self.recorder.ReadSamples( self.nSamplesRead, nSamples )
        self.nSamplesRead += nSamples
        return self.recorder.sound.dat2str( sampleArray )
    @property
    def stream( self ): 
        # attribute must be present to pass an assertion in Recognizer.listen(), 
        #and its value must have a .read() method
        return self if self.recorder else None

# source must be an instance of a speech_recognition.AudioSource subclass
# source.stream must be non-None while the source is active
# source.CHUNK must be the (integer) number of samples per chunk
# source.SAMPLE_RATE must be the sampling rate
# source.SAMPLE_WIDTH must be the number of bytes per sample
# source.stream.read(numberOfSamples) must return raw single-channel audio data







