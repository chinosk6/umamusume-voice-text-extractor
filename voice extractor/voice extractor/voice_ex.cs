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
                wavVolume = 1.0f;
                InitDict();
            }
            catch (Exception ex)
            {
                Close();
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
                                // Console.WriteLine($"anotherCueId contains - {waveName} ({cueid}), pass...");
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

        public static string GetSaveName([NotNull] string savePath, string saveFileprefix, int waveId)
        {
            return $"{savePath}/{saveFileprefix}{waveId}.wav";
        }

        public List<int> GetWaveIds()
        {
            var ret = new List<int>();
            ret.AddRange(awbReader.Waves.Select(wave => wave.WaveId));
            return ret;
        }

        public string ExtractAudioFromWaveId([NotNull] string savePath, string saveFileprefix, int waveId)
        {
            if (!Directory.Exists(savePath))
            {
                Directory.CreateDirectory(savePath);
            }

            UmaWaveStream copy = new(awbReader, waveId);
            copy.Loop = false;
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

        public string ExtractAudioFromCueId([NotNull] string savePath, string saveFileprefix, int cueId, int gender = 0)
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
                if (srcBytes == null) return -1;
                if (searchBytes == null) return -1;
                if (srcBytes.Length == 0) return -1;
                if (searchBytes.Length == 0) return -1;
                if (srcBytes.Length < searchBytes.Length) return -1;

                for (int i = 0; i < srcBytes.Length - searchBytes.Length; i++)
                {
                    if (srcBytes[i] == searchBytes[0])
                    {
                        if (searchBytes.Length == 1)
                        {
                            return i;
                        }

                        bool flag = true;
                        for (int j = 1; j < searchBytes.Length; j++)
                        {
                            if (srcBytes[i + j] != searchBytes[j])
                            {
                                flag = false;
                                break;
                            }
                        }

                        if (flag)
                        {
                            return i;
                        }
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

        public static void CutWavFile(string fileName, string saveName, ulong startMs, ulong endMs)
        {
            var savePath = System.IO.Path.GetDirectoryName(saveName);
            if (savePath != null && !Directory.Exists(savePath))
            {
                Directory.CreateDirectory(savePath);
            }

            using (var reader = new WaveFileReader(fileName))
            {
                var fileLength = (int)reader.Length;
                using (var writer = new WaveFileWriter(saveName, reader.WaveFormat))
                {
                    var cutFromStart = TimeSpan.FromMilliseconds(startMs);
                    var cutFromEnd = TimeSpan.FromMilliseconds(endMs);
                    var bytesPerMillisecond = reader.WaveFormat.AverageBytesPerSecond / 1000f;
                    var startPos = (int)Math.Round(cutFromStart.TotalMilliseconds * bytesPerMillisecond);
                    startPos -= startPos % reader.WaveFormat.BlockAlign;
                    var endPos = (int)Math.Round(cutFromEnd.TotalMilliseconds * bytesPerMillisecond);
                    endPos -= endPos % reader.WaveFormat.BlockAlign;
                    endPos = endPos > fileLength ? fileLength : endPos;
                    TrimWavFile(reader, writer, startPos, endPos);
                }
            }
        }

        public static List<string> CutWavFileBatch(string fileName, string saveNamePrefix, List<List<ulong>> timeMsList)
        {
            var savePath = System.IO.Path.GetDirectoryName(saveNamePrefix);
            if (savePath != null && !Directory.Exists(savePath))
            {
                Directory.CreateDirectory(savePath);
            }

            var ret = new List<string>();
            using (var reader = new WaveFileReader(fileName))
            {
                foreach (var i in timeMsList)
                {
                    if (i.Count != 2) throw new ArgumentException("timeMsList must be List<List[ulong, ulong]>");
                    var saveName = $"{saveNamePrefix}_{timeMsList.IndexOf(i)}.wav";
                    ret.Add(saveName);
                    var startMs = i[0];
                    var endMs = i[1];

                    var fileLength = (int)reader.Length;
                    using (WaveFileWriter writer = new WaveFileWriter(saveName,
                               reader.WaveFormat))
                    {
                        var cutFromStart = TimeSpan.FromMilliseconds(startMs);
                        var cutFromEnd = TimeSpan.FromMilliseconds(endMs);
                        var bytesPerMillisecond = reader.WaveFormat.AverageBytesPerSecond / 1000f;
                        var startPos = (int)Math.Round(cutFromStart.TotalMilliseconds * bytesPerMillisecond);
                        startPos -= startPos % reader.WaveFormat.BlockAlign;
                        var endPos = (int)Math.Round(cutFromEnd.TotalMilliseconds * bytesPerMillisecond);
                        endPos -= endPos % reader.WaveFormat.BlockAlign;
                        endPos = endPos > fileLength ? fileLength : endPos;
                        TrimWavFile(reader, writer, startPos, endPos, false);
                    }
                }
            }

            return ret;
        }

        private static void TrimWavFile(WaveFileReader reader, WaveFileWriter writer, int startPos, int endPos,
            bool dispose = true)
        {
            reader.Position = startPos;
            var buffer = new byte[1024];
            while (reader.Position < endPos)
            {
                var bytesRequired = (int)(endPos - reader.Position);
                if (bytesRequired <= 0) continue;
                var bytesToRead = Math.Min(bytesRequired, buffer.Length);
                var bytesRead = reader.Read(buffer, 0, bytesToRead);
                if (bytesRead > 0)
                {
                    writer.Write(buffer, 0, bytesRead);
                }
            }

            if (!dispose) return;
            reader.Dispose();
            writer.Dispose();
        }

        public static void ResampleWav(string fileName, string saveName, int rate, int bits, int channels)
        {
            var savePath = Path.GetDirectoryName(saveName);
            if (savePath != null)
            {
                Directory.CreateDirectory(savePath);
            }

            using (var reader = new WaveFileReader(fileName))
            {
                var convertedStream = new MediaFoundationResampler(reader,
                    new WaveFormat(rate, bits, channels));
                var wavSampleProvider = convertedStream.ToSampleProvider();
                WaveFileWriter.CreateWaveFile16(saveName,
                    new VolumeSampleProvider(wavSampleProvider)
                    {
                        Volume = 1.0f
                    });
            }
        }

        private static float GetRms(AudioFileReader audioFileReader)
        {
            const int blockSize = 1024;
            var buffer = new float[blockSize];
            double sumSquared = 0;
            int read;
            var samplesCount = 0;

            do
            {
                read = audioFileReader.Read(buffer, 0, blockSize);
                for (var i = 0; i < read; i++)
                {
                    if (buffer[i] > 0)
                    {
                        var sampleDb = 20 * Math.Log10(buffer[i]);
                        if (sampleDb > -40)
                        {
                            sumSquared += buffer[i] * buffer[i];
                            samplesCount++;
                        }
                    }
                }
            } while (read > 0);

            var rms = Math.Sqrt(sumSquared / samplesCount);
            audioFileReader.Position = 0;
            return Convert.ToSingle(rms);
        }

        public static float CalculateVolumeGain(float musicRms, float voiceRms, float plusVoiceDb)
        {
            // 将音乐和人声的RMS值转换为分贝（dB）
            var musicDb = (float)(20 * Math.Log10(musicRms));
            var voiceDb = (float)(20 * Math.Log10(voiceRms));
            // 计算音量增益（音乐音量加2dB）
            var volumeGainDb = musicDb + plusVoiceDb - voiceDb;
            // 将音量增益转换为线性值
            var volumeGain = (float)Math.Pow(10, volumeGainDb / 20);
            return volumeGain;
        }

        public static void MixWav(List<string> files, string saveName, float volume)
        {
            var readers = new List<AudioFileReader>();
            var nowIndex = 0;
            var musicRms = 0.0f;
            foreach (var reader in files.Select(file => new AudioFileReader(file)))
            {
                if (nowIndex > 0)
                {
                    if (volume >= 0)
                    {
                        reader.Volume = volume;
                    }
                    else
                    {
                        if (volume <= -2.0)
                        {
                            var voiceRms = GetRms(reader);
                            reader.Volume = CalculateVolumeGain(musicRms, voiceRms, 0.0f);
                            // Console.WriteLine($"volume {saveName}: {musicRms}, {voiceRms} {reader.Volume}");
                        }
                    }
                }
                else
                {
                    musicRms = GetRms(reader);
                }

                readers.Add(reader);
                nowIndex++;
            }

            var mixer = new MixingSampleProvider(readers);
            WaveFileWriter.CreateWaveFile16(saveName, mixer);
            // WaveFileWriter.CreateWaveFile(saveName, mixer.ToWaveProvider());
            foreach (var reader in readers)
            {
                reader.Dispose();
            }
        }

        public static void RemoveAudioSilence(string fileName)
        {
            ulong startMs;
            ulong endMs;
            using (var reader = new AudioFileReader(fileName))
            {
                var durationEnd = reader.GetSilenceDuration(AudioFileReaderExt.SilenceLocation.End);
                var durationStart = reader.GetSilenceDuration(AudioFileReaderExt.SilenceLocation.Start);
                startMs = (ulong)durationStart.TotalMilliseconds;
                var endKeepMs = (ulong)durationEnd.TotalMilliseconds;
                endMs = (ulong)reader.TotalTime.TotalMilliseconds - endKeepMs;
            }

            var tempName = $"temp/{Path.GetFileName(fileName)}";
            CutWavFile(fileName, tempName, startMs, endMs);
            File.Delete(fileName);
            File.Move(tempName, fileName);
        }

        public static void ConcatenateWavFiles(string outputFile, IEnumerable<string> sourceFiles)
        {
            var buffer = new byte[1024];
            WaveFileWriter waveFileWriter = null;

            try
            {
                foreach (var sourceFile in sourceFiles)
                {
                    using (var reader = new WaveFileReader(sourceFile))
                    {
                        if (waveFileWriter == null)
                        {
                            // first time in create new Writer
                            waveFileWriter = new WaveFileWriter(outputFile, reader.WaveFormat);
                        }
                        else
                        {
                            if (!reader.WaveFormat.Equals(waveFileWriter.WaveFormat))
                            {
                                throw new InvalidOperationException(
                                    "Can't concatenate WAV Files that don't share the same format"
                                );
                            }
                        }

                        int read;
                        while ((read = reader.Read(buffer, 0, buffer.Length)) > 0)
                        {
                            waveFileWriter.Write(buffer, 0, read);
                        }
                    }
                }
            }
            finally
            {
                waveFileWriter?.Dispose();
            }
        }

        public static void SilenceWavPartsByActivePos(string fileName, string saveName, List<List<ulong>> activeMs)
        {
            var savePath = Path.GetDirectoryName(saveName);
            if (savePath != null && !Directory.Exists(savePath))
            {
                Directory.CreateDirectory(savePath);
            }

            using (WaveFileReader reader = new(fileName))
            using (WaveFileWriter writer = new(saveName, reader.WaveFormat))
            {
                int read;
                var buffer = new byte[1024];
                while ((read = reader.Read(buffer, 0, buffer.Length)) > 0)
                {
                    var nowMs = (reader.Position - reader.Position % reader.WaveFormat.BlockAlign) /
                                (reader.WaveFormat.AverageBytesPerSecond / 1000d);
                    if (activeMs.Any(mList => nowMs > mList[0] && nowMs < mList[1]))
                    {
                        writer.Write(buffer, 0, read);
                    }
                    else
                    {
                        writer.Write(new byte[1024], 0, read);
                    }
                    // Console.WriteLine($"nowMs: {fileName} - {nowMs}");
                }
            }
        }

        public static void AdjustVolume(string filePath, List<Dictionary<string, object>> volumeChanges,
            string outputFilePath)
        {
            var savePath = Path.GetDirectoryName(outputFilePath);
            if (savePath != null && !Directory.Exists(savePath))
            {
                Directory.CreateDirectory(savePath);
            }

            using (var reader = new WaveFileReader(filePath))
            {
                using (var writer = new WaveFileWriter(outputFilePath, reader.WaveFormat))
                {
                    int read;
                    var buffer = new byte[1024];
                    var currentPosition = 0.0;

                    while ((read = reader.Read(buffer, 0, buffer.Length)) > 0)
                    {
                        var currentTime = currentPosition / (double)reader.WaveFormat.AverageBytesPerSecond * 1000.0;
                        var volumeChange = volumeChanges.Find(c =>
                            currentTime >= Convert.ToDouble(c["start"]) && currentTime <= Convert.ToDouble(c["end"]));

                        if (volumeChange != null)
                        {
                            var dbChange = Convert.ToSingle(volumeChange["db"]);
                            AdjustVolume(buffer, read, dbChange);
                        }

                        writer.Write(buffer, 0, read);
                        currentPosition += read;
                    }
                }
            }
        }

        private static void AdjustVolume(byte[] buffer, int length, float dbChange)
        {
            // 计算音量缩放因子
            var scale = (float)Math.Pow(10, dbChange / 20.0);

            // 将字节数组转换为浮点数数组
            var samples = new float[length / 2];
            for (int i = 0; i < length / 2; i++)
            {
                samples[i] = BitConverter.ToInt16(buffer, i * 2) / 32768f;
            }

            // 缩放音频样本
            for (int i = 0; i < samples.Length; i++)
            {
                samples[i] *= scale;
            }

            // 将浮点数数组转换回字节数组
            for (int i = 0; i < samples.Length; i++)
            {
                var value = (short)(samples[i] * 32768);
                buffer[i * 2] = (byte)(value & 0xFF);
                buffer[i * 2 + 1] = (byte)(value >> 8);
            }
        }

        public void Close()
        {
            acbFile?.Dispose();
            awbFile?.Dispose();
            acbReader?.Dispose();
            awbReader?.Dispose();
        }
    }

    internal static class AudioFileReaderExt
    {
        public enum SilenceLocation
        {
            Start,
            End
        }

        private static bool IsSilence(float amplitude, sbyte threshold)
        {
            double dB = 20 * Math.Log10(Math.Abs(amplitude));
            return dB < threshold;
        }

        public static TimeSpan GetSilenceDuration(this AudioFileReader reader,
            SilenceLocation location,
            sbyte silenceThreshold = -40)
        {
            var counter = 0;
            var volumeFound = false;
            var eof = false;
            var oldPosition = reader.Position;

            var buffer = new float[reader.WaveFormat.SampleRate * 4];
            while (!volumeFound && !eof)
            {
                var samplesRead = reader.Read(buffer, 0, buffer.Length);
                if (samplesRead == 0)
                    eof = true;

                for (var n = 0; n < samplesRead; n++)
                {
                    if (IsSilence(buffer[n], silenceThreshold))
                    {
                        counter++;
                    }
                    else
                    {
                        if (location == SilenceLocation.Start)
                        {
                            volumeFound = true;
                            break;
                        }
                        else if (location == SilenceLocation.End)
                        {
                            counter = 0;
                        }
                    }
                }
            }

            // reset position
            reader.Position = oldPosition;

            var silenceSamples = (double)counter / reader.WaveFormat.Channels;
            var silenceDuration = (silenceSamples / reader.WaveFormat.SampleRate) * 1000;
            return TimeSpan.FromMilliseconds(silenceDuration);
        }
    }
}
