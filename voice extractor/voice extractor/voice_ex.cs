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

            var saveName = $"{savePath}/{saveFileprefix}{waveId}.wav";
            WaveFileWriter.CreateWaveFile16(saveName,
                new VolumeSampleProvider(copy.ToSampleProvider())
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

