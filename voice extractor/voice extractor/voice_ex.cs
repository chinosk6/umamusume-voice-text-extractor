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
                acbReader = new AcbReader(acbFile);

                awbFile = File.OpenRead(awbPath);
                awbReader = new AwbReader(awbFile);
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
        
        public static string GetSaveName([NotNull]string savePath, string saveFileprefix, int waveId)
        {
            return $"{savePath}/{saveFileprefix}{waveId}.wav";
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

            var saveName = GetSaveName(savePath, saveFileprefix, waveId);
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

        public static ulong GetStreamCriAuthKey(string umaInstallPath)
        {
            int IndexOf(byte[] srcBytes, byte[] searchBytes)  
            {  
                if (srcBytes == null) { return -1; }  
                if (searchBytes == null) { return -1; }  
                if (srcBytes.Length == 0) { return -1; }  
                if (searchBytes.Length == 0) { return -1; }  
                if (srcBytes.Length < searchBytes.Length) { return -1; }  
                for (int i = 0; i < srcBytes.Length - searchBytes.Length; i++)  
                {  
                    if (srcBytes[i] == searchBytes[0])  
                    {  
                        if (searchBytes.Length == 1) { return i; }  
                        bool flag = true;  
                        for (int j = 1; j < searchBytes.Length; j++)  
                        {  
                            if (srcBytes[i + j] != searchBytes[j])  
                            {  
                                flag = false;  
                                break;  
                            }  
                        }  
                        if (flag) { return i; }  
                    }  
                }  
                return -1;  
            }  
            
            var assetPath = $"{umaInstallPath}/umamusume_Data/resources.assets";
            var fileS = File.OpenRead(assetPath);
            var fileBytes = new byte[fileS.Length];
            fileS.Read(fileBytes, 0, fileBytes.Length);

            byte[] authFlag = { 0x63, 0x72, 0x69, 0x5f, 0x61, 0x75, 0x74, 0x68 };
            byte[] numBytes = { 0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39 };
            const byte stopFlag = 0x73;
            var keyStr = "";

            var flagStartPos = IndexOf(fileBytes, authFlag);
            
            var stopFlg = true;
            while (stopFlg)
            {
                var nowByte = fileBytes[flagStartPos];
                if (numBytes.Contains(nowByte))
                {
                    keyStr = $"{(char)nowByte}{keyStr}";
                } 
                else if (nowByte.Equals(stopFlag))
                {
                    stopFlg = false;
                }
                flagStartPos--;
            }
            return ulong.Parse(keyStr);
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

