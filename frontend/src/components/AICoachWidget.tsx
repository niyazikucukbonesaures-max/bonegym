import { useState, useMemo, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, Dumbbell, Clock, Zap, CheckCircle, XCircle, TrendingUp, Heart, Target, RefreshCw, Flame, Star, Settings, Info, X } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

// ─── Types ────────────────────────────────────────────────────────────────────

interface Exercise {
  name: string
  sets?: number
  reps?: string
  duration?: string
  rest?: string
  notes?: string
  alternatives?: string[]  // Alternatif egzersizler
}

interface WarmUpStep {
  name: string
  duration: string
  notes?: string
}

interface WorkoutPlan {
  type: string
  title: string
  intensity: 'low' | 'moderate' | 'high'
  duration: number
  motivation: string
  warmUp: string
  warmUpSteps?: WarmUpStep[]  // Detaylı ısınma adımları
  coolDown: string
  exercises: Exercise[]
  tips: string[]
}

interface SportProfile {
  sport_type: string
  training_frequency: number
  training_intensity: string
  is_athlete: boolean
}

// ─── Strength Plans ───────────────────────────────────────────────────────────

const STRENGTH_PLANS: WorkoutPlan[] = [
  {
    type: 'strength',
    title: 'Üst Vücut Güç Antrenmanı',
    intensity: 'high',
    duration: 60,
    motivation: 'Bugün sınırlarını zorla! Her tekrar seni daha güçlü yapıyor.',
    warmUp: '5 dk hafif koşu + kol çevirmeler + omuz açıcı hareketler',
    coolDown: '5 dk statik germe: göğüs, omuz, sırt kasları',
    exercises: [
      { name: 'Bench Press (Düz Baskı)', sets: 4, reps: '6-8', rest: '3 dk', notes: 'Ağırlığı kontrollü indir' },
      { name: 'Barbell Row (Barbell Kürek)', sets: 4, reps: '6-8', rest: '3 dk', notes: 'Sırtı düz tut' },
      { name: 'Overhead Press (Omuz Presi)', sets: 3, reps: '8-10', rest: '2 dk', notes: 'Core sıkı' },
      { name: 'Pull-Up (Barfiks)', sets: 3, reps: 'Maks', rest: '2 dk', notes: 'Tam hareket açıklığı' },
      { name: 'Dips (Paralel Bar)', sets: 3, reps: '10-12', rest: '90 sn' },
      { name: 'Bicep Curl (Dumbbell)', sets: 3, reps: '10-12', rest: '60 sn' },
      { name: 'Tricep Pushdown', sets: 3, reps: '12-15', rest: '60 sn' },
    ],
    tips: [
      'Progresif aşırı yüklenme prensibini uygula',
      'Her sette son 1-2 tekrar zorlu olmalı',
      'Antrenman öncesi yeterli karbonhidrat al',
    ],
  },
  {
    type: 'strength',
    title: 'Alt Vücut Güç Antrenmanı',
    intensity: 'high',
    duration: 65,
    motivation: 'Bacak günü karakteri ortaya çıkarır. Vazgeçme!',
    warmUp: '5 dk bisiklet + dinamik bacak açıcılar + kalça aktivasyonu',
    coolDown: '5 dk kuadriseps, hamstring ve kalça germe',
    exercises: [
      { name: 'Squat (Barbell)', sets: 5, reps: '5', rest: '3 dk', notes: 'Paralelin altına in' },
      { name: 'Romanian Deadlift', sets: 4, reps: '8-10', rest: '2.5 dk', notes: 'Hamstringi hisset' },
      { name: 'Leg Press', sets: 3, reps: '10-12', rest: '2 dk' },
      { name: 'Bulgarian Split Squat', sets: 3, reps: '10 (her bacak)', rest: '90 sn', notes: 'Denge ve güç' },
      { name: 'Leg Curl (Makine)', sets: 3, reps: '12-15', rest: '60 sn' },
      { name: 'Calf Raise', sets: 4, reps: '15-20', rest: '60 sn', notes: 'Tam hareket açıklığı' },
    ],
    tips: [
      'Squat derinliğine dikkat et',
      'Diz ve ayak parmakları aynı yönde olmalı',
      'Antrenman sonrası protein alımını unutma',
    ],
  },
  {
    type: 'strength',
    title: 'Tam Vücut Güç Antrenmanı',
    intensity: 'high',
    duration: 70,
    motivation: 'Tüm vücudunu çalıştır, maksimum güç kazan!',
    warmUp: '5 dk genel ısınma + eklem hareketleri',
    coolDown: '5-10 dk tam vücut germe',
    exercises: [
      { name: 'Deadlift (Konvansiyonel)', sets: 4, reps: '5', rest: '3 dk', notes: 'Kral egzersiz' },
      { name: 'Bench Press', sets: 4, reps: '6-8', rest: '2.5 dk' },
      { name: 'Squat', sets: 4, reps: '6-8', rest: '3 dk' },
      { name: 'Barbell Row', sets: 3, reps: '8-10', rest: '2 dk' },
      { name: 'Overhead Press', sets: 3, reps: '8-10', rest: '2 dk' },
      { name: 'Plank', sets: 3, duration: '60 sn', rest: '60 sn' },
    ],
    tips: [
      'Büyük bileşik hareketlere öncelik ver',
      'Yeterli uyku güç gelişimi için kritik',
      'Haftalık 2-3 kez bu antrenmanı uygula',
    ],
  },
  {
    type: 'strength',
    title: 'Push Day (İtme Günü)',
    intensity: 'high',
    duration: 55,
    motivation: 'İt, bastır, güçlen! Bugün göğüs ve omuzlar yanacak.',
    warmUp: '5 dk ısınma + rotator cuff aktivasyonu',
    coolDown: 'Göğüs ve omuz germe hareketleri',
    exercises: [
      { name: 'Incline Bench Press', sets: 4, reps: '8-10', rest: '2.5 dk' },
      { name: 'Flat Dumbbell Press', sets: 3, reps: '10-12', rest: '2 dk' },
      { name: 'Overhead Press (Dumbbell)', sets: 4, reps: '10-12', rest: '2 dk' },
      { name: 'Lateral Raise', sets: 3, reps: '15-20', rest: '60 sn' },
      { name: 'Cable Fly', sets: 3, reps: '12-15', rest: '60 sn' },
      { name: 'Skull Crusher', sets: 3, reps: '12-15', rest: '60 sn' },
      { name: 'Tricep Overhead Extension', sets: 3, reps: '12-15', rest: '60 sn' },
    ],
    tips: [
      'Göğüs kasını sıkıştırmaya odaklan',
      'Omuz sağlığı için rotator cuff egzersizleri ekle',
    ],
  },
  {
    type: 'strength',
    title: 'Pull Day (Çekme Günü)',
    intensity: 'high',
    duration: 55,
    motivation: 'Sırt ve bisepsler için tam gaz! Çek ve güçlen.',
    warmUp: '5 dk ısınma + sırt aktivasyonu',
    coolDown: 'Sırt ve biseps germe',
    exercises: [
      { name: 'Deadlift', sets: 3, reps: '5-6', rest: '3 dk', notes: 'Ağır ve kontrollü' },
      { name: 'Pull-Up / Lat Pulldown', sets: 4, reps: '8-10', rest: '2 dk' },
      { name: 'Seated Cable Row', sets: 4, reps: '10-12', rest: '2 dk' },
      { name: 'Face Pull', sets: 3, reps: '15-20', rest: '60 sn', notes: 'Omuz sağlığı için' },
      { name: 'Barbell Curl', sets: 3, reps: '10-12', rest: '60 sn' },
      { name: 'Hammer Curl', sets: 3, reps: '12-15', rest: '60 sn' },
      { name: 'Rear Delt Fly', sets: 3, reps: '15', rest: '60 sn' },
    ],
    tips: [
      'Sırt kasını hissetmeye çalış, sadece kolu değil',
      'Kürek kemiklerini sıkıştır',
    ],
  },
]

// ─── Endurance Plans ──────────────────────────────────────────────────────────

const ENDURANCE_PLANS: WorkoutPlan[] = [
  {
    type: 'endurance',
    title: 'Interval Koşu Antrenmanı',
    intensity: 'high',
    duration: 45,
    motivation: 'Her interval seni daha hızlı yapıyor. Acıya katlan, sonuç gelecek!',
    warmUp: '10 dk hafif koşu + dinamik germe',
    coolDown: '10 dk yürüyüş + statik germe',
    exercises: [
      { name: '400m Sprint', sets: 8, duration: '90 sn', rest: '90 sn', notes: 'Maksimum efor' },
      { name: 'Aktif Dinlenme (Yürüyüş)', duration: '90 sn', notes: 'Nefes topla' },
    ],
    tips: [
      'Her intervalda aynı tempoyu koru',
      'Nefes kontrolüne dikkat et',
      'Antrenman sonrası elektrolit al',
    ],
  },
  {
    type: 'endurance',
    title: 'Uzun Mesafe Koşusu',
    intensity: 'moderate',
    duration: 75,
    motivation: 'Uzun koşular dayanıklılığının temelidir. Sakin ol, devam et!',
    warmUp: '5 dk yürüyüş + hafif koşu',
    coolDown: '5 dk yürüyüş + bacak germe',
    exercises: [
      { name: 'Uzun Koşu', duration: '60-70 dk', notes: 'Konuşabilir tempoda (Zone 2)' },
    ],
    tips: [
      'Konuşabilir tempoda koş (Zone 2)',
      'Her 20-30 dk su iç',
      'Haftada 1 kez uzun koşu yeterli',
    ],
  },
  {
    type: 'endurance',
    title: 'Tempo Koşusu',
    intensity: 'high',
    duration: 50,
    motivation: 'Tempo koşusu laktik eşiğini yükseltir. Zorlu ama değer!',
    warmUp: '10 dk hafif koşu',
    coolDown: '10 dk hafif koşu + germe',
    exercises: [
      { name: 'Tempo Koşusu', duration: '20-30 dk', notes: 'Rahatsız ama sürdürülebilir tempo (Zone 3-4)' },
    ],
    tips: [
      'Tempo koşusu "rahatsız ama sürdürülebilir" hissettirmeli',
      'Haftada 1-2 kez yeterli',
      'Kalp atış hızını takip et',
    ],
  },
  {
    type: 'endurance',
    title: 'Tepe Antrenmanı (Hill Training)',
    intensity: 'high',
    duration: 50,
    motivation: 'Tepeler seni güçlendirir! Her çıkış bir zafer.',
    warmUp: '10 dk düz zeminde koşu',
    coolDown: '10 dk yürüyüş + germe',
    exercises: [
      { name: 'Tepe Koşusu', sets: 8, duration: '30-45 sn', rest: '2 dk', notes: 'Maksimum efor ile çık' },
      { name: 'Yürüyerek İniş', duration: '2 dk', notes: 'Aktif dinlenme' },
    ],
    tips: [
      'Tepe koşuları bacak gücünü ve VO2max\'ı artırır',
      'Öne eğil, kısa adımlar at',
      'Haftada 1 kez yeterli',
    ],
  },
  {
    type: 'endurance',
    title: 'Toparlanma Koşusu',
    intensity: 'low',
    duration: 35,
    motivation: 'Toparlanma da antrenmanın parçası. Hafif koş, dinlen!',
    warmUp: '3 dk yürüyüş',
    coolDown: '5 dk yürüyüş + germe',
    exercises: [
      { name: 'Hafif Koşu', duration: '25-30 dk', notes: 'Çok rahat tempo (Zone 1-2)' },
    ],
    tips: [
      'Bu antrenman kasları aktif olarak dinlendirir',
      'Konuşabilir tempoda ol',
      'Yoğun antrenman sonrası ertesi gün ideal',
    ],
  },
]

// ─── Bodybuilding Plans ───────────────────────────────────────────────────────

const BODYBUILDING_PLANS: WorkoutPlan[] = [
  {
    type: 'bodybuilding',
    title: 'Göğüs & Triceps Günü',
    intensity: 'high',
    duration: 65,
    motivation: 'Göğüs günü! Pump hissini maksimize et, her kası hisset.',
    warmUp: '5 dk kardio + omuz açıcı hareketler',
    coolDown: 'Göğüs ve triceps germe',
    exercises: [
      { name: 'Flat Barbell Bench Press', sets: 4, reps: '8-12', rest: '90 sn', notes: 'Kas-zihin bağlantısı' },
      { name: 'Incline Dumbbell Press', sets: 4, reps: '10-12', rest: '90 sn' },
      { name: 'Cable Crossover / Pec Deck', sets: 3, reps: '12-15', rest: '60 sn', notes: 'Sıkıştır' },
      { name: 'Decline Push-Up', sets: 3, reps: 'Maks', rest: '60 sn' },
      { name: 'Tricep Pushdown (Kablo)', sets: 4, reps: '12-15', rest: '60 sn' },
      { name: 'Overhead Tricep Extension', sets: 3, reps: '12-15', rest: '60 sn' },
      { name: 'Dips (Tricep odaklı)', sets: 3, reps: '10-15', rest: '60 sn' },
    ],
    tips: [
      'Her tekrarda kası hissetmeye odaklan',
      'Pump için kısa dinlenme süreleri kullan',
      'Antrenman sonrası protein shake iç',
    ],
  },
  {
    type: 'bodybuilding',
    title: 'Sırt & Biceps Günü',
    intensity: 'high',
    duration: 65,
    motivation: 'Geniş bir sırt güç ve estetik demek. Çek ve büyü!',
    warmUp: '5 dk ısınma + sırt aktivasyonu',
    coolDown: 'Sırt ve biceps germe',
    exercises: [
      { name: 'Wide Grip Pull-Up', sets: 4, reps: '8-12', rest: '90 sn' },
      { name: 'Barbell Row', sets: 4, reps: '8-12', rest: '90 sn', notes: 'Kürek kemiklerini sıkıştır' },
      { name: 'Lat Pulldown (Geniş tutuş)', sets: 3, reps: '10-12', rest: '75 sn' },
      { name: 'Seated Cable Row', sets: 3, reps: '12-15', rest: '75 sn' },
      { name: 'Single Arm Dumbbell Row', sets: 3, reps: '12 (her taraf)', rest: '60 sn' },
      { name: 'Barbell Curl', sets: 4, reps: '10-12', rest: '75 sn' },
      { name: 'Incline Dumbbell Curl', sets: 3, reps: '12-15', rest: '60 sn' },
      { name: 'Concentration Curl', sets: 3, reps: '12-15', rest: '60 sn' },
    ],
    tips: [
      'Sırt kasını hisset, sadece kolu değil',
      'Tam hareket açıklığı kullan',
    ],
  },
  {
    type: 'bodybuilding',
    title: 'Bacak Günü',
    intensity: 'high',
    duration: 70,
    motivation: 'Bacak günü karakteri ortaya çıkarır. Ağla ama çalış!',
    warmUp: '10 dk bisiklet + dinamik bacak açıcılar',
    coolDown: 'Kuadriseps, hamstring, kalça germe',
    exercises: [
      { name: 'Barbell Squat', sets: 4, reps: '10-12', rest: '2 dk', notes: 'Tam derinlik' },
      { name: 'Leg Press', sets: 4, reps: '12-15', rest: '90 sn' },
      { name: 'Hack Squat', sets: 3, reps: '12-15', rest: '90 sn' },
      { name: 'Romanian Deadlift', sets: 4, reps: '10-12', rest: '90 sn', notes: 'Hamstring germe' },
      { name: 'Leg Curl (Yatay)', sets: 3, reps: '12-15', rest: '75 sn' },
      { name: 'Leg Extension', sets: 3, reps: '15-20', rest: '60 sn' },
      { name: 'Standing Calf Raise', sets: 4, reps: '15-20', rest: '60 sn' },
      { name: 'Seated Calf Raise', sets: 3, reps: '20-25', rest: '60 sn' },
    ],
    tips: [
      'Bacak günü atlamak yasak!',
      'Yeterli karbonhidrat al',
      'DOMS normaldir, devam et',
    ],
  },
  {
    type: 'bodybuilding',
    title: 'Omuz Günü',
    intensity: 'moderate',
    duration: 55,
    motivation: 'Geniş omuzlar V-şeklini tamamlar. Bugün omuzlar yanacak!',
    warmUp: '5 dk ısınma + rotator cuff aktivasyonu',
    coolDown: 'Omuz germe hareketleri',
    exercises: [
      { name: 'Seated Dumbbell Press', sets: 4, reps: '10-12', rest: '90 sn' },
      { name: 'Lateral Raise', sets: 4, reps: '15-20', rest: '60 sn', notes: 'Kontrollü indir' },
      { name: 'Front Raise', sets: 3, reps: '12-15', rest: '60 sn' },
      { name: 'Rear Delt Fly (Makine)', sets: 4, reps: '15-20', rest: '60 sn' },
      { name: 'Face Pull', sets: 3, reps: '15-20', rest: '60 sn', notes: 'Omuz sağlığı' },
      { name: 'Upright Row', sets: 3, reps: '12-15', rest: '75 sn' },
      { name: 'Shrug (Trapez)', sets: 3, reps: '15-20', rest: '60 sn' },
    ],
    tips: [
      'Lateral raise\'de dirsekleri hafif bükük tut',
      'Arka omuz ihmal edilmemeli',
    ],
  },
  {
    type: 'bodybuilding',
    title: 'Kol Günü (Biceps & Triceps)',
    intensity: 'moderate',
    duration: 50,
    motivation: 'Kol günü! Pump hissini maksimize et, kollar şişecek!',
    warmUp: '5 dk ısınma + dirsek eklem hareketleri',
    coolDown: 'Kol germe hareketleri',
    exercises: [
      { name: 'Barbell Curl', sets: 4, reps: '10-12', rest: '75 sn' },
      { name: 'Hammer Curl', sets: 3, reps: '12-15', rest: '60 sn' },
      { name: 'Preacher Curl', sets: 3, reps: '12-15', rest: '60 sn' },
      { name: 'Cable Curl', sets: 3, reps: '15-20', rest: '60 sn' },
      { name: 'Close Grip Bench Press', sets: 4, reps: '10-12', rest: '90 sn' },
      { name: 'Skull Crusher', sets: 3, reps: '12-15', rest: '75 sn' },
      { name: 'Tricep Pushdown', sets: 3, reps: '15-20', rest: '60 sn' },
      { name: 'Overhead Tricep Extension', sets: 3, reps: '12-15', rest: '60 sn' },
    ],
    tips: [
      'Süperset yaparak pump\'ı artır',
      'Tam hareket açıklığı kullan',
    ],
  },
]

// ─── CrossFit Plans ───────────────────────────────────────────────────────────

const CROSSFIT_PLANS: WorkoutPlan[] = [
  {
    type: 'crossfit',
    title: 'WOD: Fırtına',
    intensity: 'high',
    duration: 45,
    motivation: 'CrossFit sınırları yıkar! Bugün fırtına gibi çalış!',
    warmUp: '400m koşu + 10 air squat + 10 push-up + 10 sit-up (2 tur)',
    coolDown: '5 dk yürüyüş + tam vücut germe',
    exercises: [
      { name: 'Burpee', sets: 5, reps: '10', rest: '30 sn', notes: 'Tam hareket' },
      { name: 'Box Jump', sets: 5, reps: '10', rest: '30 sn', notes: 'Güvenli iniş' },
      { name: 'Kettlebell Swing', sets: 5, reps: '15', rest: '30 sn', notes: 'Kalça ile it' },
      { name: 'Pull-Up', sets: 5, reps: '8', rest: '30 sn' },
      { name: 'Wall Ball', sets: 5, reps: '15', rest: '30 sn' },
    ],
    tips: [
      'Teknik bozulmadan önce dur',
      'Nefes kontrolü kritik',
      'Skoru not al, gelişimi takip et',
    ],
  },
  {
    type: 'crossfit',
    title: 'WOD: Dayanıklılık Testi',
    intensity: 'high',
    duration: 40,
    motivation: 'AMRAP zamanı! Kaç tur yapabilirsin? Kendini zorla!',
    warmUp: '5 dk genel ısınma + hareketlilik',
    coolDown: '5 dk germe',
    exercises: [
      { name: 'AMRAP 20 dk:', notes: '20 dakika boyunca mümkün olduğunca çok tur' },
      { name: '- Thruster (Barbell)', reps: '10', notes: '43kg erkek / 29kg kadın' },
      { name: '- Toes-to-Bar', reps: '10' },
      { name: '- Double Under (İp Atlama)', reps: '20', notes: 'Yoksa 40 single under' },
    ],
    tips: [
      'Sürdürülebilir bir tempo seç',
      'Hareketler arasında kısa mola ver',
    ],
  },
  {
    type: 'crossfit',
    title: 'WOD: Güç & Kondisyon',
    intensity: 'high',
    duration: 50,
    motivation: 'Güç ve kondisyonu birleştir! CrossFit\'in özü bu!',
    warmUp: '10 dk genel ısınma + barbell aktivasyonu',
    coolDown: '10 dk germe ve mobilite',
    exercises: [
      { name: 'Clean & Jerk', sets: 5, reps: '3', rest: '2 dk', notes: 'Teknik önce' },
      { name: 'For Time (3 tur):', notes: 'Mümkün olduğunca hızlı tamamla' },
      { name: '- Deadlift', reps: '15', notes: '100kg erkek / 70kg kadın' },
      { name: '- Handstand Push-Up', reps: '12', notes: 'Yoksa pike push-up' },
      { name: '- Box Jump', reps: '15' },
      { name: '- Row (Kürek Makinesi)', duration: '250m' },
    ],
    tips: [
      'Olympic lifting tekniğine yatırım yap',
      'Mobilite çalışmalarını ihmal etme',
    ],
  },
  {
    type: 'crossfit',
    title: 'Güç Odaklı WOD',
    intensity: 'high',
    duration: 55,
    motivation: 'Bugün ağır kaldır! Güç CrossFit\'in temeli.',
    warmUp: '10 dk ısınma + barbell aktivasyonu',
    coolDown: '10 dk germe',
    exercises: [
      { name: 'Back Squat', sets: 5, reps: '5', rest: '3 dk', notes: 'Ağır, kontrollü' },
      { name: 'Strict Press', sets: 5, reps: '5', rest: '2.5 dk' },
      { name: 'Deadlift', sets: 3, reps: '5', rest: '3 dk' },
      { name: 'Metcon (10 dk AMRAP):', notes: 'Güç sonrası kondisyon' },
      { name: '- Kettlebell Goblet Squat', reps: '10' },
      { name: '- Push-Up', reps: '10' },
      { name: '- Sit-Up', reps: '15' },
    ],
    tips: [
      'Güç antrenmanı CrossFit performansını artırır',
      'Ağırlığı kademeli artır',
    ],
  },
  {
    type: 'crossfit',
    title: 'Kardio WOD',
    intensity: 'high',
    duration: 40,
    motivation: 'Kardio günü! Kalp atışını hissettir, ter dök!',
    warmUp: '5 dk hafif koşu + dinamik hareketler',
    coolDown: '5 dk yürüyüş + germe',
    exercises: [
      { name: 'For Time:', notes: 'Mümkün olduğunca hızlı tamamla' },
      { name: '- Koşu', duration: '400m' },
      { name: '- Burpee', reps: '30' },
      { name: '- Koşu', duration: '400m' },
      { name: '- Kettlebell Swing', reps: '40', notes: '24kg erkek / 16kg kadın' },
      { name: '- Koşu', duration: '400m' },
      { name: '- Box Jump', reps: '30' },
      { name: '- Koşu', duration: '400m' },
    ],
    tips: [
      'Koşu temposunu sabit tut',
      'Hareketler arasında nefes topla',
    ],
  },
]

// ─── Powerlifting Plans ───────────────────────────────────────────────────────

const POWERLIFTING_PLANS: WorkoutPlan[] = [
  {
    type: 'powerlifting',
    title: 'Squat Odaklı Antrenman',
    intensity: 'high',
    duration: 75,
    motivation: 'Squat kraldır! Bugün bacaklar ve sırt maksimum güce ulaşacak.',
    warmUp: '10 dk ısınma + squat aktivasyonu + hafif setler',
    coolDown: 'Kalça fleksörü ve kuadriseps germe',
    exercises: [
      { name: 'Back Squat (Ana Hareket)', sets: 5, reps: '3-5', rest: '4 dk', notes: '%85-90 1RM ile çalış' },
      { name: 'Pause Squat', sets: 3, reps: '3', rest: '3 dk', notes: 'Dibinde 2 sn dur' },
      { name: 'Box Squat', sets: 3, reps: '5', rest: '3 dk', notes: 'Patlayıcı kalkış' },
      { name: 'Romanian Deadlift (Yardımcı)', sets: 3, reps: '8', rest: '2 dk' },
      { name: 'Leg Press', sets: 3, reps: '10', rest: '2 dk' },
      { name: 'Core: Plank', sets: 3, duration: '60 sn', rest: '60 sn' },
    ],
    tips: [
      'Squat derinliğini asla feda etme',
      'Bel kemeri kullanımını öğren',
      'Progresif aşırı yüklenme şart',
    ],
  },
  {
    type: 'powerlifting',
    title: 'Bench Press Odaklı Antrenman',
    intensity: 'high',
    duration: 65,
    motivation: 'Bench press gücün göstergesi! Bugün göğüs ve triceps maksimuma çıkıyor.',
    warmUp: '5 dk ısınma + omuz aktivasyonu + hafif bench setleri',
    coolDown: 'Göğüs ve omuz germe',
    exercises: [
      { name: 'Bench Press (Ana Hareket)', sets: 5, reps: '3-5', rest: '4 dk', notes: '%85-90 1RM' },
      { name: 'Pause Bench Press', sets: 3, reps: '3', rest: '3 dk', notes: 'Göğüste 1 sn dur' },
      { name: 'Close Grip Bench Press', sets: 3, reps: '6-8', rest: '2.5 dk' },
      { name: 'Dumbbell Fly', sets: 3, reps: '10-12', rest: '90 sn' },
      { name: 'Tricep Pushdown', sets: 4, reps: '10-12', rest: '90 sn' },
      { name: 'Face Pull (Omuz sağlığı)', sets: 3, reps: '15-20', rest: '60 sn' },
    ],
    tips: [
      'Sırt kavisi ve ayak pozisyonuna dikkat et',
      'Rotator cuff egzersizlerini ihmal etme',
    ],
  },
  {
    type: 'powerlifting',
    title: 'Deadlift Odaklı Antrenman',
    intensity: 'high',
    duration: 70,
    motivation: 'Deadlift tüm vücudu çalıştırır! Bugün zemin sarsılacak.',
    warmUp: '10 dk ısınma + kalça aktivasyonu + hafif deadlift setleri',
    coolDown: 'Sırt, hamstring ve kalça germe',
    exercises: [
      { name: 'Conventional Deadlift (Ana)', sets: 4, reps: '3-5', rest: '4 dk', notes: '%85-90 1RM' },
      { name: 'Deficit Deadlift', sets: 3, reps: '4', rest: '3 dk', notes: '5cm platform üzerinde' },
      { name: 'Romanian Deadlift', sets: 3, reps: '6-8', rest: '2.5 dk' },
      { name: 'Barbell Row', sets: 4, reps: '6-8', rest: '2 dk' },
      { name: 'Pull-Up', sets: 3, reps: '8-10', rest: '2 dk' },
      { name: 'Hyperextension', sets: 3, reps: '12-15', rest: '90 sn' },
    ],
    tips: [
      'Sırtı düz tut, bel bükülmemeli',
      'Bel kemeri ağır setlerde kullan',
      'Deadlift haftada 1-2 kez yeterli',
    ],
  },
  {
    type: 'powerlifting',
    title: 'Yardımcı Egzersiz Günü',
    intensity: 'moderate',
    duration: 60,
    motivation: 'Yardımcı egzersizler zayıf noktalarını güçlendirir!',
    warmUp: '5 dk ısınma + eklem hareketleri',
    coolDown: 'Tam vücut germe',
    exercises: [
      { name: 'Good Morning', sets: 4, reps: '8-10', rest: '2 dk', notes: 'Sırt ve hamstring' },
      { name: 'Bulgarian Split Squat', sets: 3, reps: '10 (her bacak)', rest: '90 sn' },
      { name: 'Dumbbell Row', sets: 4, reps: '10-12', rest: '90 sn' },
      { name: 'Overhead Press', sets: 4, reps: '8-10', rest: '2 dk' },
      { name: 'Glute Bridge', sets: 3, reps: '15', rest: '60 sn' },
      { name: 'Ab Wheel Rollout', sets: 3, reps: '10-12', rest: '60 sn' },
    ],
    tips: [
      'Yardımcı egzersizler ana hareketleri destekler',
      'Zayıf noktalarına odaklan',
    ],
  },
  {
    type: 'powerlifting',
    title: 'Deload Haftası',
    intensity: 'low',
    duration: 45,
    motivation: 'Deload dinlenmek değil, toparlanmaktır. Akıllı antrenman!',
    warmUp: '5 dk ısınma',
    coolDown: '10 dk germe ve mobilite',
    exercises: [
      { name: 'Squat (%60 1RM)', sets: 3, reps: '5', rest: '2 dk', notes: 'Teknik odaklı' },
      { name: 'Bench Press (%60 1RM)', sets: 3, reps: '5', rest: '2 dk' },
      { name: 'Deadlift (%60 1RM)', sets: 3, reps: '3', rest: '2 dk' },
      { name: 'Mobilite Çalışması', duration: '15 dk', notes: 'Kalça, omuz, sırt' },
    ],
    tips: [
      'Deload her 4-6 haftada bir yapılmalı',
      'Ağırlığı düşür, tekniği mükemmelleştir',
      'Uyku ve beslenmeye özen göster',
    ],
  },
]

// ─── Beginner Plans (Yeni Başlayan) ──────────────────────────────────────────

const BEGINNER_PLANS: WorkoutPlan[] = [
  {
    type: 'beginner',
    title: 'Yeni Başlayan: Tam Vücut A',
    intensity: 'low',
    duration: 30,
    motivation: 'Her büyük yolculuk tek bir adımla başlar. Bugün o adımı at! 🌱',
    warmUp: '5 dk yürüyüş + hafif kol ve bacak açıcı hareketler',
    coolDown: '5 dk hafif germe — tüm büyük kas grupları',
    exercises: [
      { name: 'Vücut Ağırlığı Squat', sets: 3, reps: '10-12', rest: '90 sn', notes: 'Diz ayak parmağını geçmesin' },
      { name: 'Duvara Şınav (Wall Push-Up)', sets: 3, reps: '10-12', rest: '60 sn', notes: 'Omuzlar düz, core sıkı' },
      { name: 'Dumbbell Kürek (Hafif)', sets: 3, reps: '10', rest: '60 sn', notes: '5-8 kg ile başla' },
      { name: 'Plank (Diz Üstü)', sets: 3, duration: '20-30 sn', rest: '60 sn', notes: 'Bel düz tut' },
      { name: 'Yürüyüş / Hafif Koşu', duration: '10 dk', notes: 'Rahat tempo' },
    ],
    tips: [
      'Haftada 3 gün, aralarında 1 gün dinlenme',
      'Ağırlık değil teknik önemli — önce formu öğren',
      'Her antrenman sonrası protein al (yumurta, yoğurt)',
      'İlk 4 haftada ağırlık artırmana gerek yok',
    ],
  },
  {
    type: 'beginner',
    title: 'Yeni Başlayan: Tam Vücut B',
    intensity: 'low',
    duration: 30,
    motivation: 'Dünden daha iyisin. Devam et! 💪',
    warmUp: '5 dk yürüyüş + eklem ısınma hareketleri',
    coolDown: '5 dk germe',
    exercises: [
      { name: 'Lunge (Öne Adım)', sets: 3, reps: '8 (her bacak)', rest: '90 sn', notes: 'Denge için yavaş yap' },
      { name: 'Dumbbell Omuz Presi (Oturarak)', sets: 3, reps: '10', rest: '75 sn', notes: '4-6 kg ile başla' },
      { name: 'Lat Pulldown (Hafif Ağırlık)', sets: 3, reps: '12', rest: '75 sn', notes: 'Sırtı hisset' },
      { name: 'Crunch', sets: 3, reps: '15', rest: '45 sn', notes: 'Boynu zorlaştırma' },
      { name: 'Bisiklet / Yürüyüş', duration: '10 dk', notes: 'Hafif tempo' },
    ],
    tips: [
      'A ve B antrenmanlarını dönüşümlü yap',
      'Uyku en az 7-8 saat olmalı',
      'Su içmeyi unutma — günde 2-3 litre',
    ],
  },
  {
    type: 'beginner',
    title: 'Yeni Başlayan: Kardio & Hareket',
    intensity: 'low',
    duration: 25,
    motivation: 'Hareket etmek yeterli — mükemmel olmak zorunda değilsin! 🚶',
    warmUp: '3 dk yürüyüş',
    coolDown: '5 dk germe',
    exercises: [
      { name: 'Tempolu Yürüyüş', duration: '15 dk', notes: 'Hafif nefes açılması hissettirmeli' },
      { name: 'Jumping Jack (Yavaş)', sets: 3, reps: '15', rest: '60 sn', notes: 'Ritim önemli' },
      { name: 'Diz Kaldırma (High Knees Yavaş)', sets: 3, duration: '20 sn', rest: '40 sn' },
      { name: 'Yan Plank (Diz Üstü)', sets: 2, duration: '20 sn (her taraf)', rest: '45 sn' },
    ],
    tips: [
      'Nefes almayı unutma — zorlanırsan yavaşla',
      'Bu antrenman haftada 2-3 kez yapılabilir',
      'Zamanla süreyi ve yoğunluğu artır',
    ],
  },
  {
    type: 'beginner',
    title: 'Yeni Başlayan: Üst Vücut Temelleri',
    intensity: 'low',
    duration: 28,
    motivation: 'Küçük adımlar büyük değişimler yaratır. Bugün üst vücut! 🌟',
    warmUp: '5 dk ısınma + omuz çevirme hareketleri',
    coolDown: 'Göğüs, omuz, sırt germe',
    exercises: [
      { name: 'Duvara Şınav', sets: 3, reps: '12', rest: '60 sn', notes: 'Güçlendikçe eğimi artır' },
      { name: 'Dumbbell Bicep Curl (Hafif)', sets: 3, reps: '12', rest: '60 sn', notes: '4-6 kg' },
      { name: 'Dumbbell Lateral Raise (Hafif)', sets: 3, reps: '12', rest: '60 sn', notes: '3-4 kg, kontrollü' },
      { name: 'Seated Row (Makine, Hafif)', sets: 3, reps: '12', rest: '75 sn', notes: 'Kürek kemiklerini sıkıştır' },
      { name: 'Plank', sets: 3, duration: '25 sn', rest: '45 sn' },
    ],
    tips: [
      'Ağırlık seçimi: Son 2 tekrar zorlu ama yapılabilir olmalı',
      'Haftada 2 kez üst vücut yeterli',
    ],
  },
  {
    type: 'beginner',
    title: 'Yeni Başlayan: Alt Vücut Temelleri',
    intensity: 'low',
    duration: 28,
    motivation: 'Güçlü bacaklar sağlıklı bir yaşamın temelidir! 🦵',
    warmUp: '5 dk yürüyüş + dinamik bacak açıcılar',
    coolDown: 'Kuadriseps, hamstring, baldır germe',
    exercises: [
      { name: 'Vücut Ağırlığı Squat', sets: 3, reps: '12-15', rest: '90 sn', notes: 'Sandalyeye oturur gibi' },
      { name: 'Glute Bridge', sets: 3, reps: '15', rest: '60 sn', notes: 'Kalçayı sık' },
      { name: 'Step-Up (Basamak)', sets: 3, reps: '10 (her bacak)', rest: '75 sn', notes: 'Alçak basamakla başla' },
      { name: 'Calf Raise (Vücut Ağırlığı)', sets: 3, reps: '20', rest: '45 sn' },
      { name: 'Yürüyüş', duration: '8 dk', notes: 'Soğuma yürüyüşü' },
    ],
    tips: [
      'Squat yaparken topuklar yerden kalkmasın',
      'Haftada 2 kez alt vücut yeterli',
      'Bacak kasları büyük — iyi beslenme şart',
    ],
  },
]

const GENERAL_PLANS: WorkoutPlan[] = [
  {
    type: 'general',
    title: 'Tam Vücut Fitness Antrenmanı',
    intensity: 'moderate',
    duration: 50,
    motivation: 'Genel fitness için mükemmel bir antrenman! Her kas grubu çalışacak.',
    warmUp: '5 dk hafif koşu + dinamik germe hareketleri',
    coolDown: '5 dk statik germe',
    exercises: [
      { name: 'Squat (Vücut ağırlığı veya barbell)', sets: 3, reps: '12-15', rest: '90 sn' },
      { name: 'Push-Up', sets: 3, reps: '12-15', rest: '60 sn' },
      { name: 'Dumbbell Row', sets: 3, reps: '12 (her taraf)', rest: '60 sn' },
      { name: 'Dumbbell Shoulder Press', sets: 3, reps: '12-15', rest: '60 sn' },
      { name: 'Lunge', sets: 3, reps: '10 (her bacak)', rest: '60 sn' },
      { name: 'Plank', sets: 3, duration: '45 sn', rest: '45 sn' },
      { name: 'Bicycle Crunch', sets: 3, reps: '20', rest: '45 sn' },
    ],
    tips: [
      'Haftada 3 kez bu antrenmanı uygula',
      'Ağırlıkları kademeli artır',
      'Yeterli su iç',
    ],
  },
  {
    type: 'general',
    title: 'Kardio & Kondisyon',
    intensity: 'moderate',
    duration: 40,
    motivation: 'Kalp sağlığın için en iyi yatırım! Bugün kardio zamanı.',
    warmUp: '5 dk yürüyüş',
    coolDown: '5 dk yürüyüş + germe',
    exercises: [
      { name: 'Koşu veya Bisiklet', duration: '20-25 dk', notes: 'Orta tempo (Zone 2-3)' },
      { name: 'Jumping Jack', sets: 3, reps: '30', rest: '30 sn' },
      { name: 'High Knees', sets: 3, duration: '30 sn', rest: '30 sn' },
      { name: 'Mountain Climber', sets: 3, duration: '30 sn', rest: '30 sn' },
    ],
    tips: [
      'Haftada 3-5 kez kardio yap',
      'Kalp atış hızını takip et',
      'Çeşitlilik motivasyonu artırır',
    ],
  },
  {
    type: 'general',
    title: 'Core & Karın Antrenmanı',
    intensity: 'moderate',
    duration: 35,
    motivation: 'Güçlü core her şeyin temelidir! Bugün karın kasları yanacak.',
    warmUp: '5 dk hafif kardio',
    coolDown: 'Sırt ve karın germe',
    exercises: [
      { name: 'Plank', sets: 4, duration: '60 sn', rest: '30 sn' },
      { name: 'Crunch', sets: 3, reps: '20', rest: '30 sn' },
      { name: 'Leg Raise', sets: 3, reps: '15', rest: '45 sn' },
      { name: 'Russian Twist', sets: 3, reps: '20 (her taraf)', rest: '30 sn' },
      { name: 'Dead Bug', sets: 3, reps: '10 (her taraf)', rest: '45 sn' },
      { name: 'Side Plank', sets: 3, duration: '45 sn (her taraf)', rest: '30 sn' },
      { name: 'Mountain Climber', sets: 3, duration: '30 sn', rest: '30 sn' },
    ],
    tips: [
      'Core antrenmanı haftada 3-4 kez yapılabilir',
      'Nefes kontrolü önemli',
      'Bel ağrısı varsa doktora danış',
    ],
  },
  {
    type: 'general',
    title: 'Mobilite & Esneklik',
    intensity: 'low',
    duration: 40,
    motivation: 'Esneklik uzun vadeli sağlığın anahtarı. Bugün vücuduna iyi bak!',
    warmUp: '5 dk hafif yürüyüş',
    coolDown: 'Derin nefes egzersizleri',
    exercises: [
      { name: 'Kalça Fleksörü Germe', duration: '60 sn (her taraf)', notes: 'Derin nefes al' },
      { name: 'Hamstring Germe', duration: '60 sn (her taraf)' },
      { name: 'Göğüs Açıcı', duration: '60 sn' },
      { name: 'Omuz Germe', duration: '45 sn (her taraf)' },
      { name: 'Pigeon Pose (Güvercin Pozu)', duration: '90 sn (her taraf)' },
      { name: 'Cat-Cow (Kedi-İnek)', sets: 3, reps: '10', notes: 'Sırt mobilite' },
      { name: 'Thoracic Rotation', sets: 3, reps: '10 (her taraf)' },
      { name: 'Ankle Circles', sets: 2, reps: '10 (her yön)' },
    ],
    tips: [
      'Mobilite çalışması her gün yapılabilir',
      'Ağrı hissedersen dur',
      'Yoga veya pilates ekleyebilirsin',
    ],
  },
  {
    type: 'general',
    title: 'HIIT Antrenmanı',
    intensity: 'high',
    duration: 35,
    motivation: 'HIIT ile kısa sürede maksimum sonuç! Hazır mısın?',
    warmUp: '5 dk hafif kardio + dinamik germe',
    coolDown: '5 dk yürüyüş + germe',
    exercises: [
      { name: 'Burpee', duration: '40 sn', rest: '20 sn', notes: 'Maks efor' },
      { name: 'Jump Squat', duration: '40 sn', rest: '20 sn' },
      { name: 'Push-Up', duration: '40 sn', rest: '20 sn' },
      { name: 'High Knees', duration: '40 sn', rest: '20 sn' },
      { name: 'Mountain Climber', duration: '40 sn', rest: '20 sn' },
      { name: 'Jumping Jack', duration: '40 sn', rest: '20 sn' },
      { name: '(4 tur tekrar et)', notes: 'Toplam ~24 dk çalışma' },
    ],
    tips: [
      'HIIT haftada 2-3 kez yeterli',
      'Dinlenme günleri önemli',
      'Yoğunluğu kademeli artır',
    ],
  },
]

// ─── Plan Selector ────────────────────────────────────────────────────────────

function getTodaysPlanForSport(sportType: string, fitnessLevel?: string): WorkoutPlan {
  const dayOfWeek = new Date().getDay() // 0=Sun, 1=Mon, ..., 6=Sat

  // Yeni başlayanlar için her zaman beginner planları kullan
  if (fitnessLevel === 'beginner') {
    return BEGINNER_PLANS[dayOfWeek % BEGINNER_PLANS.length]
  }

  switch (sportType) {
    case 'strength':
      return STRENGTH_PLANS[dayOfWeek % STRENGTH_PLANS.length]
    case 'endurance':
      return ENDURANCE_PLANS[dayOfWeek % ENDURANCE_PLANS.length]
    case 'bodybuilding':
      return BODYBUILDING_PLANS[dayOfWeek % BODYBUILDING_PLANS.length]
    case 'crossfit':
      return CROSSFIT_PLANS[dayOfWeek % CROSSFIT_PLANS.length]
    case 'powerlifting':
      return POWERLIFTING_PLANS[dayOfWeek % POWERLIFTING_PLANS.length]
    case 'mixed':
    case 'general':
    default:
      return GENERAL_PLANS[dayOfWeek % GENERAL_PLANS.length]
  }
}

function getPlansForSport(sportType: string, fitnessLevel?: string): WorkoutPlan[] {
  // Yeni başlayanlar için her zaman beginner planları
  if (fitnessLevel === 'beginner') {
    return BEGINNER_PLANS
  }

  switch (sportType) {
    case 'strength':      return STRENGTH_PLANS
    case 'endurance':     return ENDURANCE_PLANS
    case 'bodybuilding':  return BODYBUILDING_PLANS
    case 'crossfit':      return CROSSFIT_PLANS
    case 'powerlifting':  return POWERLIFTING_PLANS
    default:              return GENERAL_PLANS
  }
}

const SPORT_LABELS: Record<string, string> = {
  strength:      'Güç Antrenmanı',
  endurance:     'Dayanıklılık',
  bodybuilding:  'Vücut Geliştirme',
  crossfit:      'CrossFit',
  powerlifting:  'Powerlifting',
  mixed:         'Karma Fitness',
  general:       'Genel Fitness',
  beginner:      'Yeni Başlayan',
}

const SPORT_COLORS: Record<string, string> = {
  strength:      'from-orange-500 to-red-600',
  endurance:     'from-blue-500 to-cyan-600',
  bodybuilding:  'from-purple-500 to-pink-600',
  crossfit:      'from-yellow-500 to-orange-600',
  powerlifting:  'from-red-600 to-rose-700',
  mixed:         'from-green-500 to-teal-600',
  general:       'from-violet-500 to-indigo-600',
}

const INTENSITY_COLORS: Record<string, string> = {
  low:      'text-green-400 bg-green-400/10',
  moderate: 'text-yellow-400 bg-yellow-400/10',
  high:     'text-red-400 bg-red-400/10',
}

const INTENSITY_LABELS: Record<string, string> = {
  low:      'Düşük',
  moderate: 'Orta',
  high:     'Yüksek',
}

// ─── Exercise Row with How-To Modal ──────────────────────────────────────────

interface ExerciseRowProps {
  ex: Exercise
  index: number
}

// free-exercise-db'den egzersiz görseli çek (GitHub raw)
const EXERCISE_IMAGE_BASE = 'https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises'

// Egzersiz adı → free-exercise-db ID mapping (en yaygın egzersizler)
const EXERCISE_ID_MAP: Record<string, string> = {
  // Squat varyasyonları
  'squat': 'Barbell_Full_Squat',
  'barbell squat': 'Barbell_Full_Squat',
  'back squat': 'Barbell_Full_Squat',
  'hack squat': 'Barbell_Hack_Squat',
  'bulgarian split squat': 'Barbell_Side_Split_Squat',
  'goblet squat': 'Goblet_Squat',
  'jump squat': 'Weighted_Jump_Squat',
  'box squat': 'Barbell_Full_Squat',
  'pause squat': 'Barbell_Full_Squat',
  'air squat': 'Bodyweight_Squat',
  // Bench Press
  'bench press': 'Barbell_Bench_Press_-_Medium_Grip',
  'flat barbell bench press': 'Barbell_Bench_Press_-_Medium_Grip',
  'incline bench press': 'Barbell_Incline_Bench_Press_-_Medium_Grip',
  'incline dumbbell press': 'Dumbbell_Incline_Bench_Press',
  'flat dumbbell press': 'Dumbbell_Bench_Press',
  'close grip bench press': 'Close-Grip_Barbell_Bench_Press',
  'pause bench press': 'Barbell_Bench_Press_-_Medium_Grip',
  'decline bench press': 'Decline_Barbell_Bench_Press',
  // Deadlift
  'deadlift': 'Barbell_Deadlift',
  'conventional deadlift': 'Barbell_Deadlift',
  'romanian deadlift': 'Romanian_Deadlift',
  'deficit deadlift': 'Barbell_Deadlift',
  'sumo deadlift': 'Sumo_Deadlift',
  // Pull-Up / Lat
  'pull-up': 'Pullups',
  'pull up': 'Pullups',
  'barfiks': 'Pullups',
  'wide grip pull-up': 'Wide-Grip_Rear_Pull-Up',
  'lat pulldown': 'Wide-Grip_Lat_Pulldown',
  'lat pulldown (geniş tutuş)': 'Wide-Grip_Lat_Pulldown',
  'v-bar pulldown': 'V-Bar_Pulldown',
  'seated cable row': 'Seated_Cable_Rows',
  'cable row': 'Seated_Cable_Rows',
  // Row
  'barbell row': 'Bent_Over_Barbell_Row',
  'dumbbell row': 'Bent_Over_One-Arm_Long_Bar_Row',
  'single arm dumbbell row': 'Bent_Over_One-Arm_Long_Bar_Row',
  't-bar row': 'T-Bar_Row_with_Handle',
  // Overhead Press
  'overhead press': 'Barbell_Shoulder_Press',
  'seated dumbbell press': 'Dumbbell_Shoulder_Press',
  'dumbbell shoulder press': 'Dumbbell_Shoulder_Press',
  'military press': 'Barbell_Shoulder_Press',
  // Curl
  'barbell curl': 'Barbell_Curl',
  'dumbbell curl': 'Dumbbell_Alternate_Bicep_Curl',
  'hammer curl': 'Hammer_Curls',
  'preacher curl': 'One_Arm_Dumbbell_Preacher_Curl',
  'incline dumbbell curl': 'Incline_Dumbbell_Curl',
  'concentration curl': 'Concentration_Curls',
  'cable curl': 'Cable_Hammer_Curls_-_Rope_Attachment',
  // Tricep
  'tricep pushdown': 'Triceps_Pushdown',
  'skull crusher': 'EZ-Bar_Skullcrusher',
  'overhead tricep extension': 'Triceps_Overhead_Extension_with_Rope',
  'dips': 'Dips_-_Triceps_Version',
  'close grip bench': 'Close-Grip_Barbell_Bench_Press',
  // Shoulder
  'lateral raise': 'Side_Lateral_Raise',
  'front raise': 'Front_Dumbbell_Raise',
  'rear delt fly': 'Reverse_Flyes',
  'face pull': 'Face_Pull',
  'upright row': 'Upright_Barbell_Row',
  'shrug': 'Barbell_Shrug',
  // Leg
  'leg press': 'Leg_Press',
  'leg curl': 'Lying_Leg_Curls',
  'leg extension': 'Leg_Extensions',
  'calf raise': 'Standing_Calf_Raises',
  'standing calf raise': 'Standing_Calf_Raises',
  'seated calf raise': 'Seated_Calf_Raise',
  'lunge': 'Barbell_Lunge',
  'glute bridge': 'Barbell_Glute_Bridge',
  // Core
  'plank': 'Plank',
  'crunch': 'Crunches',
  'leg raise': 'Flat_Bench_Leg_Pull-In',
  'russian twist': 'Russian_Twist',
  'ab wheel': 'Ab_Roller',
  'hyperextension': 'Hyperextensions_Back_Extensions',
  // Cardio / HIIT
  'burpee': 'Bench_Jump',
  'push-up': 'Decline_Push-Up',
  'push up': 'Decline_Push-Up',
  'şınav': 'Decline_Push-Up',
  'jumping jack': 'Rope_Jumping',
  'mountain climber': 'Mountain_Climbers',
  'high knees': 'Running_Treadmill',
  'box jump': 'Box_Jump_Multiple_Response',
  'kettlebell swing': 'Kettlebell_Sumo_High_Pull',
  // Chest
  'cable fly': 'Cable_Crossover',
  'cable crossover': 'Cable_Crossover',
  'dumbbell fly': 'Dumbbell_Flyes',
  'pec deck': 'Butterfly',
  // Back
  'good morning': 'Good_Morning',
}

// ─── Warm-up Parser ──────────────────────────────────────────────────────────

function parseWarmUpSteps(warmUpStr: string): WarmUpStep[] {
  // "5 dk hafif koşu + kol çevirmeler + omuz açıcı hareketler" → adımlara böl
  const parts = warmUpStr.split(/\s*\+\s*/)
  return parts.map(part => {
    const durationMatch = part.match(/^(\d+[\s-]*dk)\s+(.+)$/)
    if (durationMatch) {
      return { name: durationMatch[2].trim(), duration: durationMatch[1].trim() }
    }
    // Süre belirtilmemişse
    return { name: part.trim(), duration: '2-3 dk' }
  }).filter(s => s.name.length > 0)
}

// ─── Egzersiz Alternatifleri ──────────────────────────────────────────────────

// Alet gerektiren egzersizler → alternatifler
const EXERCISE_ALTERNATIVES: Record<string, string[]> = {
  // Barbell hareketleri → dumbbell/vücut ağırlığı
  'barbell squat': ['Goblet Squat (Dumbbell)', 'Vücut Ağırlığı Squat', 'Dumbbell Squat'],
  'squat (barbell)': ['Goblet Squat (Dumbbell)', 'Vücut Ağırlığı Squat'],
  'back squat': ['Goblet Squat', 'Dumbbell Squat', 'Vücut Ağırlığı Squat'],
  'bench press': ['Dumbbell Bench Press', 'Push-Up', 'Dumbbell Fly'],
  'flat barbell bench press': ['Dumbbell Bench Press', 'Push-Up'],
  'incline bench press': ['Incline Dumbbell Press', 'Decline Push-Up'],
  'barbell row': ['Dumbbell Row', 'Seated Cable Row', 'Resistance Band Row'],
  'deadlift': ['Romanian Deadlift (Dumbbell)', 'Kettlebell Deadlift', 'Good Morning'],
  'conventional deadlift': ['Dumbbell Deadlift', 'Kettlebell Swing'],
  'overhead press': ['Dumbbell Shoulder Press', 'Arnold Press', 'Pike Push-Up'],
  'barbell curl': ['Dumbbell Curl', 'Resistance Band Curl', 'Hammer Curl'],
  'skull crusher': ['Dumbbell Tricep Extension', 'Diamond Push-Up', 'Tricep Dips'],
  'close grip bench press': ['Diamond Push-Up', 'Dumbbell Tricep Press'],
  // Makine hareketleri → serbest ağırlık/vücut ağırlığı
  'leg press': ['Dumbbell Squat', 'Goblet Squat', 'Lunge'],
  'leg curl': ['Romanian Deadlift', 'Nordic Curl', 'Glute Bridge'],
  'leg extension': ['Vücut Ağırlığı Squat', 'Step-Up', 'Lunge'],
  'lat pulldown': ['Pull-Up', 'Resistance Band Pulldown', 'Dumbbell Row'],
  'seated cable row': ['Dumbbell Row', 'Resistance Band Row', 'Inverted Row'],
  'cable crossover': ['Dumbbell Fly', 'Push-Up', 'Resistance Band Fly'],
  'cable fly': ['Dumbbell Fly', 'Push-Up'],
  'pec deck': ['Dumbbell Fly', 'Push-Up'],
  'tricep pushdown': ['Dumbbell Tricep Extension', 'Diamond Push-Up', 'Bench Dips'],
  'face pull': ['Dumbbell Rear Delt Fly', 'Resistance Band Face Pull'],
  'hack squat': ['Goblet Squat', 'Dumbbell Squat', 'Lunge'],
  // Spesifik ekipman
  'pull-up': ['Lat Pulldown (Makine)', 'Resistance Band Pull-Up', 'Inverted Row'],
  'dips': ['Bench Dips', 'Diamond Push-Up', 'Tricep Pushdown'],
  'box jump': ['Squat Jump', 'Step-Up', 'Lunge Jump'],
  'kettlebell swing': ['Dumbbell Swing', 'Romanian Deadlift', 'Hip Thrust'],
  'wall ball': ['Dumbbell Thruster', 'Squat + Press', 'Medicine Ball Slam'],
  'rowing machine': ['Dumbbell Row', 'Resistance Band Row', 'Bent Over Row'],
  'row (kürek makinesi)': ['Dumbbell Row', 'Resistance Band Row'],
  'bisiklet': ['Yürüyüş', 'Koşu', 'Jumping Jack'],
  'treadmill': ['Yürüyüş', 'Koşu (Dışarıda)', 'Jumping Jack'],
  // Yeni başlayan egzersizleri
  'vücut ağırlığı squat': ['Goblet Squat (Hafif Dumbbell)', 'Sandalyeye Oturma Hareketi', 'Step-Up'],
  'duvara şınav': ['Diz Üstü Şınav', 'İnkline Push-Up (Masa)', 'Normal Şınav'],
  'wall push-up': ['Diz Üstü Şınav', 'İnkline Push-Up', 'Normal Şınav'],
  'dumbbell kürek': ['Resistance Band Row', 'İnverted Row', 'Seated Cable Row'],
  'plank (diz üstü)': ['Normal Plank', 'Dead Bug', 'Bird Dog'],
  'glute bridge': ['Hip Thrust (Dumbbell)', 'Single Leg Glute Bridge', 'Donkey Kick'],
  'step-up': ['Lunge', 'Squat', 'Box Step-Up'],
  'calf raise (vücut ağırlığı)': ['Seated Calf Raise', 'Single Leg Calf Raise', 'Leg Press Calf Raise'],
  'dumbbell omuz presi': ['Arnold Press', 'Pike Push-Up', 'Resistance Band Press'],
  'dumbbell bicep curl': ['Hammer Curl', 'Resistance Band Curl', 'Concentration Curl'],
  'dumbbell lateral raise': ['Cable Lateral Raise', 'Resistance Band Lateral Raise', 'Upright Row'],
  'crunch': ['Sit-Up', 'Dead Bug', 'Bicycle Crunch'],
  'jumping jack': ['Step Jack (Düşük Etkili)', 'High Knees', 'Butt Kicks'],
  'high knees': ['Marching in Place', 'Jumping Jack', 'Mountain Climber'],
  'lunge': ['Reverse Lunge', 'Step-Up', 'Split Squat'],
  'dumbbell row': ['Resistance Band Row', 'Inverted Row', 'Seated Cable Row'],
  'lat pulldown (hafif ağırlık)': ['Resistance Band Pulldown', 'Inverted Row', 'Pull-Up (Assisted)'],
}

function getAlternatives(exerciseName: string): string[] {
  const lower = exerciseName.toLowerCase().replace(/\(.*?\)/g, '').trim()
  // Direkt eşleşme
  if (EXERCISE_ALTERNATIVES[lower]) return EXERCISE_ALTERNATIVES[lower]
  // Kısmi eşleşme — egzersiz adının herhangi bir kelimesi eşleşirse
  for (const [key, alts] of Object.entries(EXERCISE_ALTERNATIVES)) {
    const keyWords = key.split(' ')
    const lowerWords = lower.split(' ')
    if (keyWords.some(kw => lowerWords.some(lw => lw.length > 3 && lw.includes(kw)))) {
      return alts
    }
  }
  // Hiç eşleşme yoksa genel alternatifler döndür
  return ['Dumbbell versiyonu', 'Vücut ağırlığı versiyonu', 'Resistance band versiyonu']
}

async function fetchExerciseImage(exerciseName: string): Promise<{ imageUrl: string | null; imageUrl2: string | null; description: string | null }> {
  const lowerName = exerciseName.toLowerCase()
    .replace(/\(.*?\)/g, '')  // Parantez içini kaldır
    .trim()

  // Direkt eşleşme
  let exerciseId = EXERCISE_ID_MAP[lowerName]

  // Kısmi eşleşme
  if (!exerciseId) {
    for (const [key, id] of Object.entries(EXERCISE_ID_MAP)) {
      if (lowerName.includes(key) || key.includes(lowerName.split(' ')[0])) {
        exerciseId = id
        break
      }
    }
  }

  if (!exerciseId) return { imageUrl: null, imageUrl2: null, description: null }

  const imageUrl = `${EXERCISE_IMAGE_BASE}/${exerciseId}/0.jpg`
  const imageUrl2 = `${EXERCISE_IMAGE_BASE}/${exerciseId}/1.jpg`

  return { imageUrl, imageUrl2, description: null }
}

function ExerciseRow({ ex, index }: ExerciseRowProps) {
  const [showModal, setShowModal] = useState(false)
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [imageUrl2, setImageUrl2] = useState<string | null>(null)
  const [description, setDescription] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [imgError, setImgError] = useState(false)
  const [showAltModal, setShowAltModal] = useState(false)

  const alternatives = getAlternatives(ex.name)

  const handleShowInfo = async () => {
    setShowModal(true)
    if (imageUrl !== null || loading) return
    setLoading(true)
    const result = await fetchExerciseImage(ex.name)
    setImageUrl(result.imageUrl)
    setImageUrl2(result.imageUrl2)
    setDescription(result.description)
    setLoading(false)
  }

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.04 }}
        className="flex items-start justify-between px-3 py-2 rounded-lg bg-white/5 hover:bg-white/8 transition-colors group"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <p className="text-white text-xs font-medium truncate">{ex.name}</p>
            <button
              onClick={handleShowInfo}
              className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded text-white/30 hover:text-violet-400"
              title="Nasıl yapılır?"
            >
              <Info className="w-3 h-3" />
            </button>
          </div>
          {ex.notes && (
            <p className="text-white/40 text-xs truncate">{ex.notes}</p>
          )}
        </div>
        <div className="flex items-center gap-2 ml-2 shrink-0 text-white/50 text-xs">
          {ex.sets && <span>{ex.sets} set</span>}
          {ex.reps && <span>× {ex.reps}</span>}
          {ex.duration && !ex.sets && <span>{ex.duration}</span>}
          {ex.rest && <span className="text-white/30">| {ex.rest}</span>}
          {alternatives.length > 0 && (
            <button
              onClick={() => setShowAltModal(true)}
              className="ml-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-orange-500/15 text-orange-400 hover:bg-orange-500/25 transition-colors border border-orange-500/20"
              title="Alternatif egzersiz göster"
            >
              Alt.
            </button>
          )}
        </div>
      </motion.div>

      {/* Alternatif Egzersiz Modal */}
      <AnimatePresence>
        {showAltModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
            onClick={() => setShowAltModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="rounded-xl border border-white/[0.1] bg-[#13131a] p-5 max-w-sm w-full"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="text-[13px] font-semibold text-white">Alternatif Egzersizler</h3>
                  <p className="text-[11px] text-white/40 mt-0.5">{ex.name} yerine yapabilirsin</p>
                </div>
                <button onClick={() => setShowAltModal(false)} className="p-1 rounded text-white/40 hover:text-white/80 hover:bg-white/10">
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="space-y-2">
                {alternatives.map((alt, i) => (
                  <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-white/5 border border-white/[0.06]">
                    <span className="w-5 h-5 rounded-full bg-orange-500/20 text-orange-400 text-[10px] font-bold flex items-center justify-center shrink-0">{i + 1}</span>
                    <div className="flex-1">
                      <p className="text-white text-[12px] font-medium">{alt}</p>
                    </div>
                    <a
                      href={`https://www.youtube.com/results?search_query=${encodeURIComponent(alt + ' nasıl yapılır')}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-red-400/60 hover:text-red-400 transition-colors"
                      title="YouTube'da izle"
                    >
                      <span className="text-[10px]">▶</span>
                    </a>
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-white/30 mt-3 text-center">
                Aynı kas grubunu çalıştıran alternatifler
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Nasıl Yapılır Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
            onClick={() => setShowModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="rounded-xl border border-white/[0.1] bg-[#13131a] p-5 max-w-sm w-full"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-[14px] font-semibold text-white">{ex.name}</h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-1 rounded text-white/40 hover:text-white/80 hover:bg-white/10 transition-all"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-6 h-6 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : imageUrl && !imgError ? (
                /* İki görsel yan yana: başlangıç ve bitiş pozisyonu */
                <div className="grid grid-cols-2 gap-2 mb-4">
                  <div className="rounded-lg overflow-hidden bg-white/5">
                    <img
                      src={imageUrl}
                      alt={`${ex.name} - başlangıç`}
                      className="w-full object-cover"
                      style={{ maxHeight: 160 }}
                      onError={() => setImgError(true)}
                    />
                    <p className="text-[9px] text-white/30 text-center py-1">Başlangıç</p>
                  </div>
                  {imageUrl2 && (
                    <div className="rounded-lg overflow-hidden bg-white/5">
                      <img
                        src={imageUrl2}
                        alt={`${ex.name} - bitiş`}
                        className="w-full object-cover"
                        style={{ maxHeight: 160 }}
                      />
                      <p className="text-[9px] text-white/30 text-center py-1">Bitiş</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center py-6 mb-4 rounded-lg bg-white/5">
                  <div className="text-center">
                    <Dumbbell className="w-8 h-8 text-white/20 mx-auto mb-2" />
                    <p className="text-[11px] text-white/30">Görsel bulunamadı</p>
                  </div>
                </div>
              )}

              {/* Egzersiz detayları */}
              <div className="flex flex-wrap gap-2 mb-3">
                {ex.sets && (
                  <span className="px-2 py-1 rounded-md bg-violet-500/15 text-violet-300 text-[11px] font-medium">
                    {ex.sets} set
                  </span>
                )}
                {ex.reps && (
                  <span className="px-2 py-1 rounded-md bg-blue-500/15 text-blue-300 text-[11px] font-medium">
                    {ex.reps} tekrar
                  </span>
                )}
                {ex.duration && (
                  <span className="px-2 py-1 rounded-md bg-emerald-500/15 text-emerald-300 text-[11px] font-medium">
                    {ex.duration}
                  </span>
                )}
                {ex.rest && (
                  <span className="px-2 py-1 rounded-md bg-white/[0.06] text-white/40 text-[11px]">
                    Dinlenme: {ex.rest}
                  </span>
                )}
              </div>

              {ex.notes && (
                <p className="text-[12px] text-white/50 mb-3">💡 {ex.notes}</p>
              )}

              {description && (
                <p className="text-[11px] text-white/40 leading-relaxed line-clamp-4 mb-3">
                  {description}
                </p>
              )}

              {/* YouTube arama linki */}
              <a
                href={`https://www.youtube.com/results?search_query=${encodeURIComponent(ex.name + ' nasıl yapılır form')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-[12px] font-medium hover:bg-red-500/20 transition-colors"
              >
                ▶ YouTube'da İzle
              </a>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

// ─── Component ────────────────────────────────────────────────────────────────

interface AICoachWidgetProps {
  className?: string
}

export function AICoachWidget({ className = '' }: AICoachWidgetProps) {
  const [sportProfile, setSportProfile] = useState<SportProfile | null>(null)
  const [fitnessLevel, setFitnessLevel] = useState<string>('beginner')

  // Derive initial plan index from today's plan for the current sport type
  const getInitialIndex = (sport: string, level?: string) => {
    const todaysPlan = getTodaysPlanForSport(sport, level)
    const plans = getPlansForSport(sport, level)
    const idx = plans.findIndex(p => p.title === todaysPlan.title)
    return idx >= 0 ? idx : new Date().getDay() % plans.length
  }

  const [planIndex, setPlanIndex] = useState<number>(() => getInitialIndex('general', 'beginner'))
  const [planStatus, setPlanStatus] = useState<'pending' | 'accepted' | 'rejected'>('pending')
  const [isExpanded, setIsExpanded] = useState(false)
  const [showWarmUpDetail, setShowWarmUpDetail] = useState(false)

  // Bugün tamamlanan plan var mı kontrol et
  const todayKey = `completed_workout_${new Date().toISOString().split('T')[0]}`
  const [todayCompleted, setTodayCompleted] = useState<{title: string; duration: number; completedAt: string} | null>(() => {
    try {
      const raw = localStorage.getItem(todayKey)
      return raw ? JSON.parse(raw) : null
    } catch { return null }
  })

  // Read from localStorage on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem('sport_profile')
      if (raw) {
        const parsed = JSON.parse(raw) as SportProfile
        setSportProfile(parsed)
        setPlanIndex(getInitialIndex(parsed.sport_type, fitnessLevel))
      }
      // Profil sayfasından fitness level'ı al
      const profileRaw = localStorage.getItem('user_profile')
      if (profileRaw) {
        const profile = JSON.parse(profileRaw)
        if (profile.fitness_level) setFitnessLevel(profile.fitness_level)
      }
    } catch {
      // ignore parse errors
    }
  }, [])

  // Fallback API call if no localStorage profile
  const { data: apiProfile } = useQuery({
    queryKey: ['sport-profile-fallback'],
    queryFn: async () => {
      const res = await axios.get('/api/sport-profiles/?user_id=1')
      const profiles = res.data
      if (Array.isArray(profiles) && profiles.length > 0) return profiles[0] as SportProfile
      if (profiles && typeof profiles === 'object' && !Array.isArray(profiles)) return profiles as SportProfile
      return null
    },
    enabled: sportProfile === null,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  // Fitness level'ı API'den al
  const { data: userProfileData } = useQuery({
    queryKey: ['user-profile-fitness'],
    queryFn: async () => {
      const res = await axios.get('/api/profile/')
      return res.data
    },
    staleTime: 5 * 60 * 1000,
  })

  useEffect(() => {
    if (userProfileData?.fitness_level) {
      setFitnessLevel(userProfileData.fitness_level)
    }
  }, [userProfileData])

  useEffect(() => {
    if (!sportProfile && apiProfile) {
      setSportProfile(apiProfile)
      setPlanIndex(getInitialIndex(apiProfile.sport_type, fitnessLevel))
    }
  }, [apiProfile, sportProfile])

  const activeSportType = sportProfile?.sport_type ?? 'general'
  const plans = useMemo(() => getPlansForSport(activeSportType, fitnessLevel), [activeSportType, fitnessLevel])
  const currentPlan = useMemo(() => plans[planIndex % plans.length], [plans, planIndex])

  const handleAccept = () => {
    setPlanStatus('accepted')
    // Tamamlanan planı localStorage'a kaydet
    const today = new Date().toISOString().split('T')[0]
    const key = `completed_workout_${today}`
    const completed = {
      title: currentPlan.title,
      type: currentPlan.type,
      duration: currentPlan.duration,
      intensity: currentPlan.intensity,
      completedAt: new Date().toISOString(),
    }
    localStorage.setItem(key, JSON.stringify(completed))
    setTodayCompleted(completed)
  }
  const handleModify = () => {
    setPlanIndex(prev => (prev + 1) % plans.length)
    setPlanStatus('pending')
  }

  const sportLabel = SPORT_LABELS[activeSportType] ?? 'Genel Fitness'
  const sportGradient = SPORT_COLORS[activeSportType] ?? SPORT_COLORS.general

  return (
    <GlassCard className={`p-5 ${className}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${sportGradient} flex items-center justify-center shadow-lg`}>
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-base leading-tight">AI Antrenman Koçu</h3>
            <p className="text-white/50 text-xs">Günün antrenman planı</p>
          </div>
        </div>

        {/* Sport type badge + Değiştir butonu */}
        <div className="flex items-center gap-2">
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gradient-to-r ${sportGradient} bg-opacity-20`}>
            <Dumbbell className="w-3 h-3 text-white" />
            <span className="text-white text-xs font-medium">{sportLabel}</span>
          </div>
          <button
            onClick={() => { setPlanStatus('pending'); handleModify() }}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/40 hover:text-white/80 transition-all"
            title="Farklı plan öner"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Yeni başlayan uyarısı */}
      {fitnessLevel === 'beginner' && (
        <motion.div
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-3 flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20"
        >
          <span className="text-emerald-400 text-sm">🌱</span>
          <p className="text-emerald-300 text-xs">
            <span className="font-semibold">Yeni başlayan programı</span> — Hafif ağırlıklar, temel hareketler. Forma odaklan!
          </p>
        </motion.div>
      )}

      {/* No profile notice */}
      {!sportProfile && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 flex items-center gap-2 px-3 py-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20"
        >
          <Settings className="w-4 h-4 text-yellow-400 shrink-0" />
          <p className="text-yellow-300 text-xs">
            Spor profili bulunamadı. Genel plan gösteriliyor.{' '}
            <a href="/profile" className="underline hover:text-yellow-200 transition-colors">
              Spor profilini ayarla
            </a>
          </p>
        </motion.div>
      )}

      {/* Plan status banner */}
      <AnimatePresence mode="wait">
        {planStatus === 'accepted' && (
          <motion.div
            key="accepted"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="mb-4 px-3 py-3 rounded-lg bg-green-500/10 border border-green-500/20"
          >
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <p className="text-green-300 text-sm font-semibold">Antrenman Tamamlandı! 🎉</p>
            </div>
            <p className="text-green-400/70 text-xs ml-6">
              {currentPlan.title} · {currentPlan.duration} dk · {INTENSITY_LABELS[currentPlan.intensity]} yoğunluk
            </p>
          </motion.div>
        )}
        {planStatus === 'rejected' && (
          <motion.div
            key="rejected"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="mb-4 flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20"
          >
            <XCircle className="w-4 h-4 text-red-400" />
            <p className="text-red-300 text-sm">Plan reddedildi. Değiştirmek için <button onClick={handleModify} className="underline hover:text-red-200">farklı plan dene</button>.</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bugün tamamlanan plan varsa göster */}
      {todayCompleted && planStatus !== 'accepted' && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-3 px-3 py-2.5 rounded-lg bg-green-500/8 border border-green-500/15"
        >
          <div className="flex items-center gap-2">
            <CheckCircle className="w-3.5 h-3.5 text-green-400 shrink-0" />
            <div>
              <p className="text-green-300 text-xs font-medium">Bugün tamamlandı ✓</p>
              <p className="text-green-400/60 text-[10px]">{todayCompleted.title} · {todayCompleted.duration} dk</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Action buttons — her zaman görünür, plan kartının üstünde */}
      <div className="flex gap-2 mb-3">
        {planStatus !== 'accepted' ? (
          <>
            <Button
              variant="default"
              size="sm"
              onClick={handleAccept}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs"
            >
              <CheckCircle className="w-3.5 h-3.5 mr-1" />
              Tamamlandı ✓
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => { setPlanStatus('pending'); handleModify() }}
              className="flex-1 text-xs"
            >
              <RefreshCw className="w-3.5 h-3.5 mr-1" />
              Farklı Plan
            </Button>
          </>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={() => { setPlanStatus('pending'); handleModify() }}
            className="w-full text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1" />
            Farklı Plan Öner
          </Button>
        )}
      </div>

      {/* Plan card */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentPlan.title}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.25 }}
        >
          {/* Plan header */}
          <div className="mb-3">
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-white font-semibold text-sm">{currentPlan.title}</h4>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${INTENSITY_COLORS[currentPlan.intensity]}`}>
                  {INTENSITY_LABELS[currentPlan.intensity]}
                </span>
              </div>
            </div>

            {/* Meta info */}
            <div className="flex items-center gap-4 text-white/50 text-xs">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {currentPlan.duration} dk
              </span>
              <span className="flex items-center gap-1">
                <Flame className="w-3 h-3" />
                {currentPlan.exercises.length} egzersiz
              </span>
              <span className="flex items-center gap-1">
                <Zap className="w-3 h-3" />
                {INTENSITY_LABELS[currentPlan.intensity]} yoğunluk
              </span>
            </div>
          </div>

          {/* Motivation */}
          <div className="mb-3 px-3 py-2 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-start gap-2">
              <Star className="w-3.5 h-3.5 text-yellow-400 mt-0.5 shrink-0" />
              <p className="text-white/70 text-xs italic">{currentPlan.motivation}</p>
            </div>
          </div>

          {/* Warm-up */}
          <div className="mb-2">
            <button
              onClick={() => setShowWarmUpDetail(v => !v)}
              className="w-full flex items-center justify-between group"
            >
              <div className="flex items-center gap-2">
                <Heart className="w-3.5 h-3.5 text-pink-400 shrink-0" />
                <span className="text-white/50 text-xs font-medium uppercase tracking-wide">Isınma Hareketleri</span>
              </div>
              <span className="text-white/30 text-xs group-hover:text-white/60 transition-colors">
                {showWarmUpDetail ? '▲ Gizle' : '▼ Detay'}
              </span>
            </button>

            <AnimatePresence>
              {showWarmUpDetail ? (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-2 space-y-1.5 overflow-hidden"
                >
                  {parseWarmUpSteps(currentPlan.warmUp).map((step, i) => (
                    <div key={i} className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-pink-500/5 border border-pink-500/10">
                      <span className="w-5 h-5 rounded-full bg-pink-500/20 text-pink-400 text-[10px] font-bold flex items-center justify-center shrink-0">{i + 1}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-white/80 text-xs font-medium capitalize">{step.name}</p>
                      </div>
                      <span className="text-pink-400/60 text-[10px] shrink-0">{step.duration}</span>
                    </div>
                  ))}
                </motion.div>
              ) : (
                <p className="text-white/50 text-xs mt-1 ml-5">{currentPlan.warmUp}</p>
              )}
            </AnimatePresence>
          </div>

          {/* Exercises */}
          <div className="mb-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white/50 text-xs font-medium uppercase tracking-wide flex items-center gap-1">
                <Target className="w-3 h-3" /> Egzersizler
              </span>
              <button
                onClick={() => setIsExpanded(v => !v)}
                className="text-white/40 hover:text-white/70 text-xs transition-colors flex items-center gap-1"
              >
                {isExpanded ? 'Gizle' : 'Tümünü gör'}
                <TrendingUp className="w-3 h-3" />
              </button>
            </div>

            <div className="space-y-1.5">
              {(isExpanded ? currentPlan.exercises : currentPlan.exercises.slice(0, 4)).map((ex, i) => (
                <ExerciseRow key={i} ex={ex} index={i} />
              ))}

              {!isExpanded && currentPlan.exercises.length > 4 && (
                <p className="text-white/30 text-xs text-center py-1">
                  +{currentPlan.exercises.length - 4} egzersiz daha...
                </p>
              )}
            </div>
          </div>

          {/* Cool-down */}
          <div className="mb-3 flex items-start gap-2">
            <RefreshCw className="w-3.5 h-3.5 text-blue-400 mt-0.5 shrink-0" />
            <div>
              <span className="text-white/50 text-xs font-medium uppercase tracking-wide">Soğuma: </span>
              <span className="text-white/70 text-xs">{currentPlan.coolDown}</span>
            </div>
          </div>

          {/* Tips */}
          {currentPlan.tips.length > 0 && (
            <div className="mb-4 space-y-1">
              {currentPlan.tips.map((tip, i) => (
                <div key={i} className="flex items-start gap-1.5">
                  <CheckCircle className="w-3 h-3 text-violet-400 mt-0.5 shrink-0" />
                  <p className="text-white/50 text-xs">{tip}</p>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </AnimatePresence>

    </GlassCard>
  )
}
