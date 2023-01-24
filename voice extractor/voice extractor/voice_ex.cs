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
        private Dictionary<int, int> anotherCueIdToWaveId = new();
        
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
                var waveOrigName = acbReader.GetWaveName(wave.WaveId, 0, false);

                foreach (var waveName in waveOrigName.Split(";"))
                {
                    try
                    {
                        var cueidStrSplit = waveName.Split("_");
                        var cueidStr = cueidStrSplit[cueidStrSplit.Length - 1];
                        var cueid = int.Parse(cueidStr);
                        if (!cueIdToWaveId.ContainsKey(cueid))
                        {
                            cueIdToWaveId.Add(cueid, wave.WaveId);
                        }
                        else
                        {
                            if (anotherCueIdToWaveId.ContainsKey(cueid))
                            {
                                Console.WriteLine($"anotherCueId contains - {waveName} ({cueid}), pass...");
                            }
                            else
                            {
                                anotherCueIdToWaveId.Add(cueid, wave.WaveId);
                            }
                        }
                    }
                    catch (FormatException)
                    {

                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"convert cueid failed: {waveName} - {ex}");
                    }
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

        public string ExtractAudioFromCueId([NotNull]string savePath, string saveFileprefix, int cueId, int gender=0)
        {
            int origWaveId, anotherWaveId;

            if (!cueIdToWaveId.ContainsKey(cueId))
            {
                origWaveId = -1;
            }
            else
            {
                origWaveId = cueIdToWaveId[cueId];
            }
            
            if (!anotherCueIdToWaveId.ContainsKey(cueId))
            {
                if (origWaveId == -1)
                {
                    throw new IndexOutOfRangeException($"{savePath} {saveFileprefix} cueId: {cueId} not found!");
                }
                anotherWaveId = origWaveId;
            }
            else
            {
                anotherWaveId = anotherCueIdToWaveId[cueId];
                if (origWaveId == -1)
                {
                    origWaveId = anotherWaveId;
                }
            }
            /*
             训练员选择不同的性别会影响部分语音的内容, 这部分语音拥有相同的 CueId, 只有 voice_id 和 gender 不同
             目前没办法在 awb/acb 文件中获取到 voice_id
             经过观察发现, 在 CueId 相同的情况下, gender 值为 1 的 WaveId 总是大于 gender 值为 2 的 WaveId
             因此暂时使用下面的方案, 期待大佬们提出更好的解决方案~
             性别 0 和 2 使用较小的 WaveId, 1 使用较大的 WaveId
             */
            return ExtractAudioFromWaveId(savePath, saveFileprefix, 
                gender == 1 ? Math.Max(origWaveId, anotherWaveId) : Math.Min(origWaveId, anotherWaveId));
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

