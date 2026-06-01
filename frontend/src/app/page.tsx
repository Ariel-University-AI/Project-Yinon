import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

const features = [
  {
    href: "/find",
    icon: "🔍",
    title: "מצא אזור להשקעה",
    body: 'לא בטוח איפה לחפש? הכנס את התקציב שלך ומה חשוב לך יותר — לקבל שכ"ד חודשי או שהנכס יעלה בערך לאורך זמן. הכלי ימליץ על האזורים הטובים ביותר עבורך.',
    cta: "התחל לחפש ←",
  },
  {
    href: "/check",
    icon: "🏡",
    title: "בדוק נכס ספציפי",
    body: "מצאת דירה שמעניינת אותך? הכנס את פרטי הנכס והמחיר המבוקש — הכלי יגיד לך אם המחיר הוגן, ויציג עסקאות דומות להשוואה.",
    cta: "בדוק נכס ←",
  },
  {
    href: "/browse",
    icon: "📊",
    title: "עיין בנכסים ביישוב",
    body: "רוצה לראות מה נמכר ובכמה? בחר עיר וסנן לפי גודל וחדרים — כל העסקאות מדורגות לפי ציון כדאיות, כדי שתוכל להשוות בקלות.",
    cta: "עיין ביישוב ←",
  },
];

const journeys = [
  {
    borderColor: "border-[#1A9E3F]",
    bg: "bg-[#EAF7EE]",
    headingColor: "text-[#1A9E3F]",
    btnBg: "bg-[#1A9E3F]",
    icon: "🆕",
    title: "אני חדש, לא יודע מאיפה להתחיל",
    steps: [
      { href: "/find",   icon: "🔍", label: "מצא אזור להשקעה",    sub: "הכנס תקציב ← קבל המלצות על ערים",         num: "①" },
      { href: "/check",  icon: "🏡", label: "בדוק נכס ספציפי",     sub: "הכנס פרטי הדירה ← בדוק אם המחיר הוגן",   num: "②" },
      { href: "/browse", icon: "📊", label: "עיין בנכסים ביישוב",  sub: "ראה מה נמכר בפועל והשווה",                num: "③" },
    ],
    tip: null,
    tipBg: "",
  },
  {
    borderColor: "border-[#006AFF]",
    bg: "bg-[#EBF3FF]",
    headingColor: "text-[#006AFF]",
    btnBg: "bg-[#006AFF]",
    icon: "🏡",
    title: "מצאתי דירה ספציפית שמעניינת אותי",
    steps: [
      { href: "/check",  icon: "🏡", label: "בדוק נכס ספציפי",    sub: "הכנס עיר, מחיר, שטח, חדרים, קומה",       num: "①" },
      { href: "/browse", icon: "📊", label: "עיין בנכסים ביישוב", sub: 'השווה לעסקאות אמיתיות באותה עיר',         num: "②" },
    ],
    tip: 'טיפ: אחרי שתקבל ציון כדאיות, לחץ על "עיין בנכסים ביישוב" כדי לראות כמה שילמו שכנים על דירות דומות',
    tipBg: "bg-[#D6E9FF] text-[#003D99]",
  },
  {
    borderColor: "border-[#00A2AD]",
    bg: "bg-[#E5F7F8]",
    headingColor: "text-[#00A2AD]",
    btnBg: "bg-[#00A2AD]",
    icon: "📊",
    title: "רוצה לסקור מחירים בעיר מסוימת",
    steps: [
      { href: "/browse", icon: "📊", label: "עיין בנכסים ביישוב", sub: "בחר עיר ← סנן לפי גודל, חדרים, שנה",     num: "①" },
    ],
    tip: "טיפ: מומלץ לסנן לשנתיים האחרונות — מחירים ישנים לא תמיד משקפים את השוק היום",
    tipBg: "bg-[#CCF0F2] text-[#005F68]",
  },
];

const glossaryItems = [
  {
    title: "🎯 ציון כדאיות — מה זה ולמה חשוב?",
    content: (
      <div className="space-y-3 text-sm">
        <p>
          <strong>ציון כדאיות</strong> הוא מספר בין <strong>0 ל-100</strong> שמסכם כמה כדאי לקנות נכס מסוים.
        </p>
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="bg-muted">
              <th className="p-2 border border-border text-right">ציון</th>
              <th className="p-2 border border-border text-right">צבע</th>
              <th className="p-2 border border-border text-right">משמעות</th>
              <th className="p-2 border border-border text-right">מה לעשות?</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="p-2 border border-border">70–100</td>
              <td className="p-2 border border-border">🟢 ירוק</td>
              <td className="p-2 border border-border">כדאי מאוד</td>
              <td className="p-2 border border-border">מומלץ לבחון ברצינות</td>
            </tr>
            <tr className="bg-muted/40">
              <td className="p-2 border border-border">45–69</td>
              <td className="p-2 border border-border">🟡 צהוב</td>
              <td className="p-2 border border-border">סביר, דורש בדיקה</td>
              <td className="p-2 border border-border">בדוק לעומק לפני החלטה</td>
            </tr>
            <tr>
              <td className="p-2 border border-border">0–44</td>
              <td className="p-2 border border-border">🔴 אדום</td>
              <td className="p-2 border border-border">לא מומלץ</td>
              <td className="p-2 border border-border">המחיר כנראה גבוה מדי</td>
            </tr>
          </tbody>
        </table>
        <p>
          <strong>איך מחשבים את הציון?</strong>
          <br />💰 <strong>60%</strong> — האם המחיר הוגן?
          <br />🏙️ <strong>25%</strong> — איכות האזור (מדד סוציו-אקונומי)
          <br />💧 <strong>15%</strong> — קל לקנות ולמכור באזור? (נזילות)
        </p>
      </div>
    ),
  },
  {
    title: "💰 מחיר חזוי ופער — מה ההבדל?",
    content: (
      <div className="space-y-2 text-sm">
        <p>
          <strong>מחיר חזוי</strong> = מה מחיר השוק ההוגן לפי המודל. המודל למד מ-6,609 עסקאות אמיתיות שנמכרו בישראל.
        </p>
        <ul className="space-y-1 pr-2">
          <li>✅ <strong>פער חיובי (+)</strong> → אתה משלם פחות מהשוק → הזדמנות!</li>
          <li>⚠️ <strong>פער קרוב לאפס</strong> → מחיר הוגן</li>
          <li>❌ <strong>פער שלילי (−)</strong> → אתה משלם יותר מהשוק → מחיר גבוה</li>
        </ul>
        <p><strong>דוגמה:</strong> מחיר חזוי 2,200,000 ₪, מחיר מבוקש 2,000,000 ₪ → פער +10% → עסקה טובה!</p>
      </div>
    ),
  },
  {
    title: "📈 מגמה שנתית — מה זה אומר?",
    content: (
      <ul className="space-y-1 text-sm pr-2">
        <li>📈 <strong>+5% בשנה</strong> → המחירים עלו — טוב אם אתה מחפש שהנכס יעלה בערך</li>
        <li>📉 <strong>−2% בשנה</strong> → המחירים ירדו — כדאי לשאול למה</li>
        <li>➡️ <strong>0%</strong> → מחירים יציבים — פחות סיכון, פחות פוטנציאל</li>
      </ul>
    ),
  },
  {
    title: "🤖 המודל — איך הוא עובד?",
    content: (
      <div className="space-y-1 text-sm">
        <p><strong>המודל:</strong> XGBoost — סוג של בינה מלאכותית.</p>
        <p><strong>מה הוא למד?</strong> מ-6,609 עסקאות מרשות המיסים: שטח, חדרים, קומה, עיר, שכונה, מדד סוציו ועוד.</p>
        <p><strong>כמה הוא מדויק?</strong> R² = 0.741 → מסביר 74% מהשינויים במחיר. שגיאה ממוצעת: ~607,000 ₪</p>
      </div>
    ),
  },
];

export default function HomePage() {
  return (
    <div className="max-w-5xl mx-auto space-y-8">

      {/* Hero */}
      <div className="rounded-xl bg-gradient-to-l from-[#1277E1] to-[#006AFF] text-white px-8 py-8 shadow-lg">
        <h1 className="text-3xl font-bold tracking-tight mb-2">🏠 יועץ נדל&quot;ן חכם</h1>
        <p className="text-white/85 text-base leading-relaxed">
          כלי חינמי לניתוח השקעות נדל&quot;ן בישראל — מבוסס נתוני רשות המיסים ומודל בינה מלאכותית
        </p>
      </div>

      {/* Feature cards */}
      <section>
        <h2 className="text-xl font-bold mb-4">🚀 במה הכלי יכול לעזור לך?</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {features.map(({ href, icon, title, body, cta }) => (
            <Card
              key={href}
              className="flex flex-col hover:shadow-md hover:border-[#006AFF] transition-all duration-200"
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{icon} {title}</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col flex-1 gap-4">
                <p className="text-sm text-muted-foreground leading-relaxed flex-1">{body}</p>
                <Link
                  href={href}
                  className="inline-flex w-full items-center justify-center rounded-lg bg-[#006AFF] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#0053D6]"
                >
                  {cta}
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <Separator />

      {/* Journey map */}
      <section>
        <h2 className="text-xl font-bold mb-1">🗺️ מפת ניווט — מאיפה מתחילים?</h2>
        <p className="text-sm text-muted-foreground mb-4">בחר את המצב שמתאים לך — ותדע בדיוק לאן ללכת:</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {journeys.map(({ borderColor, bg, headingColor, btnBg, icon, title, steps, tip, tipBg }) => (
            <div key={title} className={`rounded-xl border-2 p-5 ${borderColor} ${bg}`}>
              <div className="text-3xl text-center mb-2">{icon}</div>
              <h4 className={`text-center font-bold text-sm mb-4 leading-snug ${headingColor}`}>{title}</h4>
              <div className="space-y-1">
                {steps.map(({ href, icon: si, label, sub, num }, i) => (
                  <div key={href}>
                    <Link href={href}>
                      <div className={`${btnBg} text-white rounded-md px-3 py-2 text-xs font-semibold hover:opacity-90 transition-opacity`}>
                        {num} {si} {label}
                      </div>
                    </Link>
                    <p className="text-xs text-muted-foreground px-2 pt-1 pb-2">{sub}</p>
                    {i < steps.length - 1 && (
                      <p className={`text-center font-bold ${headingColor}`}>↓</p>
                    )}
                  </div>
                ))}
              </div>
              {tip && (
                <div className={`mt-3 rounded-md p-3 text-xs leading-relaxed ${tipBg}`}>💡 {tip}</div>
              )}
            </div>
          ))}
        </div>
      </section>

      <Separator />

      {/* Quick reference */}
      <details className="group border border-border rounded-lg overflow-hidden">
        <summary className="flex items-center justify-between px-4 py-3 cursor-pointer select-none bg-white hover:bg-muted/50 transition-colors list-none font-medium">
          📌 מה כל עמוד עושה — טבלת עזר מהירה
          <span className="text-muted-foreground group-open:rotate-180 transition-transform text-xs">▼</span>
        </summary>
        <div className="px-4 py-3 border-t border-border bg-white/60 overflow-x-auto">
          <table className="w-full border-collapse text-sm min-w-[500px]">
            <thead>
              <tr className="bg-muted">
                <th className="p-2 border border-border text-right">עמוד</th>
                <th className="p-2 border border-border text-right">שאלה שהוא עונה</th>
                <th className="p-2 border border-border text-right">מה מכניסים</th>
                <th className="p-2 border border-border text-right">מה מקבלים</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="p-2 border border-border font-semibold">🔍 מצא אזור</td>
                <td className="p-2 border border-border">באיזו עיר כדאי לחפש?</td>
                <td className="p-2 border border-border">תקציב + מטרה</td>
                <td className="p-2 border border-border">רשימת ערים + ציון + גרף</td>
              </tr>
              <tr className="bg-muted/40">
                <td className="p-2 border border-border font-semibold">🏡 בדוק נכס</td>
                <td className="p-2 border border-border">האם המחיר הוגן?</td>
                <td className="p-2 border border-border">עיר + מחיר + שטח + חדרים + קומה</td>
                <td className="p-2 border border-border">ציון 0–100 + פירוט + עסקאות דומות</td>
              </tr>
              <tr>
                <td className="p-2 border border-border font-semibold">📊 עיין ביישוב</td>
                <td className="p-2 border border-border">בכמה נמכרו דירות בעיר הזו?</td>
                <td className="p-2 border border-border">עיר + פילטרים</td>
                <td className="p-2 border border-border">טבלת עסקאות + גרף מחירים</td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>

      {/* Glossary */}
      <section>
        <h2 className="text-xl font-bold mb-1">📚 מילון מושגים</h2>
        <p className="text-sm text-muted-foreground mb-4">לחץ על כל מושג כדי לקרוא הסבר פשוט</p>
        <div className="space-y-2">
          {glossaryItems.map(({ title, content }) => (
            <details key={title} className="group border border-border rounded-lg overflow-hidden">
              <summary className="flex items-center justify-between px-4 py-3 cursor-pointer select-none bg-white hover:bg-muted/50 transition-colors list-none font-medium text-sm">
                {title}
                <span className="text-muted-foreground group-open:rotate-180 transition-transform text-xs">▼</span>
              </summary>
              <div className="px-4 py-3 border-t border-border bg-white/60">{content}</div>
            </details>
          ))}
        </div>
      </section>

      {/* Tip */}
      <div className="rounded-lg border border-[#006AFF]/30 bg-[#EBF3FF] px-4 py-3 text-sm text-[#003D99]">
        💡 טיפ: אם אתה חדש בנדל&quot;ן, התחל עם &quot;מצא אזור להשקעה&quot; — הכנס תקציב וקבל המלצות מיידיות.
      </div>

    </div>
  );
}
