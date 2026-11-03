using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;
using System.Windows.Threading;
using Microsoft.Data.SqlClient;

namespace SeraSCADA;

public partial class MainWindow : Window
{
    //Sql bağlantısı
    private readonly string sqlConnectionString =
       

    private readonly HttpClient httpClient = new HttpClient { BaseAddress = new Uri("") };

    private DispatcherTimer timer;

    private readonly List<double> tempHistory = new();
    private readonly List<double> soilHistory = new();
    private const int MaxPoints = 30;

    private bool hataGosterildi = false;

    public MainWindow()
    {
        InitializeComponent();

        timer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(2) };
        timer.Tick += async (s, e) => await RefreshDataAsync();
        timer.Start();
    }

    private async System.Threading.Tasks.Task RefreshDataAsync()
    {
        try
        {
            using SqlConnection conn = new SqlConnection(sqlConnectionString);
            await conn.OpenAsync();

            string query = "SELECT TOP 1 * FROM GreenhouseData ORDER BY Id DESC";
            using SqlCommand cmd = new SqlCommand(query, conn);
            using SqlDataReader reader = await cmd.ExecuteReaderAsync();

            if (await reader.ReadAsync())
            {
                double temp = Convert.ToDouble(reader["Temperature"]);
                double hum = Convert.ToDouble(reader["Humidity"]);
                double soil = Convert.ToDouble(reader["SoilMoisture"]);
                double light = Convert.ToDouble(reader["Light"]);
                bool heater = Convert.ToBoolean(reader["Heater"]);
                bool fan = Convert.ToBoolean(reader["Fan"]);
                bool irrigation = Convert.ToBoolean(reader["Irrigation"]);
                DateTime ts = Convert.ToDateTime(reader["Timestamp"]);

                txtTemperature.Text = $"{temp:F1}°C";
                txtHumidity.Text = $"{hum:F1}%";
                txtSoilMoisture.Text = $"{soil:F1}%";
                txtLight.Text = $"{light:F0} Lux";
                txtTimestamp.Text = ts.ToString("HH:mm:ss");

                dotHeater.Fill = heater ? Brushes.OrangeRed : Brushes.Gray;
                dotFan.Fill = fan ? Brushes.DodgerBlue : Brushes.Gray;
                dotIrrigation.Fill = irrigation ? Brushes.LimeGreen : Brushes.Gray;

                // Grafik geçmişine ekle
                tempHistory.Add(temp);
                soilHistory.Add(soil);
                if (tempHistory.Count > MaxPoints) tempHistory.RemoveAt(0);
                if (soilHistory.Count > MaxPoints) soilHistory.RemoveAt(0);

                DrawChart();
            }
        }
        catch (Exception ex)
        {
            txtTimestamp.Text = "HATA";

            if (!hataGosterildi)
            {
                hataGosterildi = true;
                MessageBox.Show(ex.ToString(), "Tam Hata Detayı", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }

    private void DrawChart()
    {
        chartCanvas.Children.Clear();

        double width = chartCanvas.ActualWidth;
        double height = chartCanvas.ActualHeight;

        if (width <= 0 || height <= 0 || tempHistory.Count < 2) return;

        DrawSeries(tempHistory, width, height, Brushes.OrangeRed, 15.0, 35.0);
        DrawSeries(soilHistory, width, height, Brushes.LimeGreen, 0.0, 100.0);
    }

    private void DrawSeries(List<double> data, double width, double height, Brush color, double minVal, double maxVal)
    {
        var polyline = new Polyline
        {
            Stroke = color,
            StrokeThickness = 2
        };

        double stepX = width / (MaxPoints - 1);
        double startX = width - (data.Count - 1) * stepX;

        for (int i = 0; i < data.Count; i++)
        {
            double x = startX + i * stepX;
            double normalized = (data[i] - minVal) / (maxVal - minVal);
            normalized = Math.Clamp(normalized, 0.0, 1.0);
            double y = height - (normalized * (height - 30)) - 15; 

            polyline.Points.Add(new Point(x, y));
        }

        chartCanvas.Children.Add(polyline);
    }
    using NModbus;
using System.Net.Sockets;

private async Task<(double temp, double hum, double soil, double light, ushort actuators)> ReadFromPlcAsync()
{
    using TcpClient client = new TcpClient();
    await client.ConnectAsync("192.168.56.1", 502); 

    var factory = new ModbusFactory();
    var master = factory.CreateMaster(client);

    ushort[] regs = await master.ReadHoldingRegistersAsync(1, 0, 5);

    double temp = regs[0] / 10.0;
    double hum = regs[1] / 10.0;
    double soil = regs[2] / 10.0;
    double light = regs[3] / 10.0;
    ushort actuators = regs[4];

    return (temp, hum, soil, light, actuators);
}

private async Task WriteManualControlAsync(bool otoMod, bool heater, bool fan, bool irrigation)
{
    using TcpClient client = new TcpClient();
    await client.ConnectAsync("192.168.56.1", 502);

    var factory = new ModbusFactory();
    var master = factory.CreateMaster(client);

    await master.WriteSingleCoilAsync(1, 0, otoMod);
    await master.WriteSingleCoilAsync(1, 1, heater);
    await master.WriteSingleCoilAsync(1, 2, fan);
    await master.WriteSingleCoilAsync(1, 3, irrigation);
}
private async void btnAiPredict_Click(object sender, RoutedEventArgs e)
{
    try
    {
        btnAiPredict.IsEnabled = false;
        txtAiPrediction.Text = "Sorgulanıyor...";

        double temp = double.Parse(txtTemperature.Text.Replace("°C", ""));
        double hum = double.Parse(txtHumidity.Text.Replace("%", ""));
        double soil = double.Parse(txtSoilMoisture.Text.Replace("%", ""));
        double light = double.Parse(txtLight.Text.Replace(" Lux", ""));

        var sensorData = new
        {
            Temperature = temp,
            Humidity = hum,
            SoilMoisture = soil,
            Light = light
        };

        var response = await httpClient.PostAsJsonAsync("predict/irrigation", sensorData);
        string json = await response.Content.ReadAsStringAsync();

        using JsonDocument doc = JsonDocument.Parse(json);
        JsonElement root = doc.RootElement;

        bool needed = root.GetProperty("irrigation_needed").GetBoolean();
        double probPercent = root.GetProperty("probability_percent").GetDouble();
        bool reliable = root.GetProperty("reliable").GetBoolean();

        txtAiPrediction.Text = needed ? "🟢 SULAMA ÖNERİLİYOR" : "🔴 SULAMA GEREKMİYOR";
        txtAiProbability.Text = $"Olasılık: %{probPercent:F1}";

        if (!reliable && root.TryGetProperty("warnings", out var warnings))
        {
            txtAiReliability.Text = "⚠ " + warnings[0].GetString();
        }
        else
        {
            txtAiReliability.Text = "";
        }

        // ---- YENİ: AI KARARINI OTOMATİK OLARAK PLC'YE GÖNDER ----
        // Yalnızca sulama gerekiyorsa VE tahmin güvenilirse otomatik komut gönderilir.
        // Güvenilir olmayan (eğitim aralığı dışı) tahminlerde PLC'ye yazılmaz — güvenlik önlemi.
        if (needed && reliable)
        {
            await WriteManualControlAsync(
                otoMod: false,
                heater: tglHeater.IsChecked == true,
                fan: tglFan.IsChecked == true,
                irrigation: true
            );

            txtAiReliability.Text = "✅ Sulama komutu PLC'ye otomatik olarak gönderildi.";
        }
    }
    catch (Exception ex)
    {
        txtAiPrediction.Text = "API hatası";
        txtAiReliability.Text = ex.Message;
    }
    finally
    {
        btnAiPredict.IsEnabled = true;
    }
}
}
private async void btnFanPredict_Click(
    object sender,
    RoutedEventArgs e)
{
    try
    {
        btnFanPredict.IsEnabled = false;

        txtFanPrediction.Text = "Sorgulanıyor...";

        double temp =
            double.Parse(
                txtTemperature.Text.Replace("°C", ""));

        double hum =
            double.Parse(
                txtHumidity.Text.Replace("%", ""));

        double light =
            double.Parse(
                txtLight.Text.Replace(" Lux", ""));

        var sensorData = new
        {
            Temperature = temp,
            Humidity = hum,
            Light = light
        };

        var response =
            await httpClient.PostAsJsonAsync(
                "predict/fan",
                sensorData);

        string json =
            await response.Content.ReadAsStringAsync();

        using JsonDocument doc =
            JsonDocument.Parse(json);

        JsonElement root =
            doc.RootElement;

        if (!response.IsSuccessStatusCode)
        {
            txtFanPrediction.Text = "API hatası";
            txtFanReliability.Text =
                root.GetProperty("error").GetString();

            return;
        }

        bool needed =
            root.GetProperty("fan_needed")
                .GetBoolean();

        double probability =
            root.GetProperty("probability_percent")
                .GetDouble();

        txtFanProbability.Text =
            $"Fan Olasılığı: %{probability:F1}";

        txtFanPrediction.Text =
            needed
            ? "🟢 FAN ÇALIŞMASI ÖNERİLİYOR"
            : "🔴 FAN ÇALIŞMASI GEREKMİYOR";

       
        bool reliable =
            root.TryGetProperty(
                "reliable",
                out JsonElement reliableElement)
            && reliableElement.GetBoolean();

        if (!reliable)
        {
            txtFanReliability.Text =
                "⚠ Tahmin güvenilir değil.";
        }
        else
        {
            txtFanReliability.Text =
                "✓ Tahmin güvenilir.";
        }
    }
    catch (Exception ex)
    {
        txtFanPrediction.Text =
            "API hatası";

        txtFanReliability.Text =
            ex.Message;
    }
    finally
    {
        btnFanPredict.IsEnabled = true;
    }
}