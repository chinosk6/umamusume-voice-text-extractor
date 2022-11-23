using System.Diagnostics.CodeAnalysis;
using CriWareFormats;
using NAudio.Wave;
using NAudio.Wave.SampleProviders;
using UmaMusumeAudio;


namespace voice_extractor
{
    public class UmaVoiceEx
    {
        private AwbReader awbReader;
        private FileStream acbFile;
        private FileStream awbFile;
        private AcbReader acbReader;
        private int fileCount;
        private float wavVolume;
        private WaveFormat waveFormat;
        private Dictionary<int, int> cueIdToWaveId = new();
        
        public UmaVoiceEx(string acbPath, string awbPath)
        {
            if (!File.Exists(acbPath) || !File.Exists(awbPath))
            {
                throw new FileNotFoundException($"File not found: {acbPath} or {awbPath}");
            }

            try
            {
                acbFile = File.OpenRead(acbPath);
                acbReader = new(acbFile);

                awbFile = File.OpenRead(awbPath);
                awbReader = new(awbFile);
                fileCount = awbReader.Waves.Count;
                wavVolume = 2.0f;
                InitDict();
            }
            catch (Exception ex)
            {
                throw new Exception($"File load failed: {ex.Message}");
            }
        }

        private void InitDict()
        {
            foreach (var wave in awbReader.Waves)
            {
                string waveName = acbReader.GetWaveName(wave.WaveId, 0, false);
                try
                {
                    var cueidStrSplit = waveName.Split("_");
                    var cueidStr = cueidStrSplit[cueidStrSplit.Length - 1];
                    var cueid = int.Parse(cueidStr);
                    cueIdToWaveId.Add(cueid, wave.WaveId);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"convert cueid failed: {waveName} - {ex}");
                }

            }
        }

        public string ExtractAudioFromWaveId([NotNull]string savePath, string saveFileprefix, int waveId)
        {
            if (!Directory.Exists(savePath))
            {
                Directory.CreateDirectory(savePath);
            }
            
            UmaWaveStream copy = new(awbReader, waveId);
            ISampleProvider wavSampleProvider;
            
            if (waveFormat is not null)
            {
                var convertedStream = new MediaFoundationResampler(copy, waveFormat);
                wavSampleProvider = convertedStream.ToSampleProvider();
            }
            else
            {
                wavSampleProvider = copy.ToSampleProvider();
            }

            var saveName = $"{savePath}/{saveFileprefix}{waveId}.wav";
            WaveFileWriter.CreateWaveFile16(saveName,
                new VolumeSampleProvider(wavSampleProvider)
                {
                    Volume = wavVolume
                });
            copy.Dispose();
            return saveName;
        }
        
        public string ExtractAudioFromCueId([NotNull]string savePath, string saveFileprefix, int cueId)
        {
            if (!cueIdToWaveId.ContainsKey(cueId))
            {
                throw new IndexOutOfRangeException($"cueId: {cueId} not found!");
            }
            return ExtractAudioFromWaveId(savePath, saveFileprefix, cueIdToWaveId[cueId]);
        }

        public void SetWaveFormat(int rate, int bits, int channels)
        {
            waveFormat = new WaveFormat(rate, bits, channels);
        }
        
        public int GetAudioCount()
        {
            return fileCount;
        }

        public void SetVolume(float value)
        {
            wavVolume = value;
        }

        public void Close()
        {
            acbFile.Dispose();
            awbFile.Dispose();
            acbReader.Dispose();
            awbReader.Dispose();
        }
        
    }
}

