# Refine - CSV Analytics Web Application

A modern, feature-rich CSV analytics platform built with Next.js 16, offering powerful data visualization, analysis, and insights generation capabilities.

![Next.js](https://img.shields.io/badge/Next.js-16.1.6-black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-4.0-38bdf8)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- **📊 Interactive Dashboard** - Comprehensive analytics dashboard with real-time data visualization
- **📈 Multiple Chart Types** - Pie charts, bar charts, line graphs, and activity statistics
- **📁 CSV Upload & Processing** - Easy drag-and-drop CSV file upload with instant analysis
- **🎨 Beautiful UI** - Clean, modern interface with smooth animations and transitions
- **🔍 Data Profiling** - Automatic data quality analysis and statistical profiling
- **🧹 Data Cleaning** - Built-in tools for handling missing values and data transformation
- **📊 Custom Visualizations** - Create and customize various chart types based on your data
- **💾 Project Management** - Save, organize, and revisit your analytics projects
- **📋 Templates** - Pre-built templates for common data analysis scenarios
- **🎯 Insights Generation** - AI-powered insights and pattern detection
- **📱 Responsive Design** - Fully responsive layout for desktop, tablet, and mobile devices

## 🚀 Tech Stack

- **Framework:** Next.js 16.1.6 (App Router)
- **Language:** TypeScript 5.0
- **Styling:** Tailwind CSS v4
- **Animations:** Framer Motion
- **Icons:** Icons8 (50+ custom icons)
- **UI Components:** Custom component library
- **Charts:** Custom SVG-based visualizations

## 📦 Installation

1. **Clone the repository**
```bash
git clone https://github.com/hwkxhh/refinex.git
cd refinex
```

2. **Install dependencies**
```bash
npm install
# or
yarn install
# or
pnpm install
```

3. **Run the development server**
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

4. **Open your browser**
```
http://localhost:3000
```

## 🎯 Usage

### Uploading CSV Files
1. Navigate to the Dashboard
2. Click the "Upload CSV" button
3. Drag and drop your CSV file or click to browse
4. View instant data preview and statistics

### Creating Projects
1. Go to Projects page
2. Click "New Project"
3. Upload your CSV data
4. Choose analysis type (Profile, Clean, or Insights)
5. Configure analysis parameters
6. Generate visualizations and reports

### Using Templates
1. Navigate to Templates page
2. Browse available templates
3. Select a template matching your use case
4. Upload your data to auto-configure the analysis

## 📂 Project Structure

```
csv-analytics-app/
├── app/
│   ├── auth/                 # Authentication pages
│   │   ├── login/
│   │   ├── signup/
│   │   └── onboarding/
│   ├── dashboard/            # Dashboard pages
│   │   ├── billing/
│   │   ├── help/
│   │   ├── projects/
│   │   ├── settings/
│   │   ├── templates/
│   │   ├── upload/
│   │   └── project/[id]/     # Dynamic project pages
│   ├── globals.css           # Global styles and theme
│   ├── layout.tsx
│   └── page.tsx              # Landing page
├── components/
│   ├── layout/               # Layout components
│   │   ├── sidebar.tsx
│   │   └── dashboard-header.tsx
│   └── ui/                   # Reusable UI components
│       ├── button.tsx
│       ├── card.tsx
│       ├── input.tsx
│       └── ...
├── lib/
│   ├── mock-data/            # Mock data for development
│   └── utils.ts              # Utility functions
├── public/
│   └── icons8/               # Icons8 icon library
└── README.md
```

## 🎨 Design System

### Color Palette
- **Primary Purple:** `#5B4FE7`
- **Secondary Purple:** `#7367F0`
- **Background:** `#F5F6FA`
- **Card Background:** `#FFFFFF`
- **Border:** `#E6E7F0`
- **Text Primary:** `#333333`
- **Text Secondary:** `#6B7280`

### Typography
- **Font Family:** System fonts (Inter, SF Pro, Segoe UI)
- **Border Radius:** 0.75rem (12px)
- **Spacing Scale:** Tailwind default scale

## 🔧 Configuration

### Environment Variables
Create a `.env.local` file in the root directory:

```env
NEXT_PUBLIC_APP_URL=http://localhost:3000
# Add other environment variables as needed
```

## 📄 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## 🌟 Key Features Breakdown

### Dashboard
- Credit card overview with transaction history
- Exchange rates monitoring
- Income vs. Expense tracking
- Efficiency metrics (86.3% overall efficiency)
- Recent transaction list
- User profile management

### Data Analysis
- Automatic column type detection
- Missing value analysis
- Statistical summaries (mean, median, mode, std dev)
- Outlier detection
- Correlation analysis

### Visualizations
- Interactive pie charts
- Stacked bar charts
- Line graphs with trend lines
- Activity statistics
- Custom chart builder

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Icons by [Icons8](https://icons8.com)
- Built with [Next.js](https://nextjs.org)
- Styled with [Tailwind CSS](https://tailwindcss.com)
- Animations by [Framer Motion](https://www.framer.com/motion/)

## 📧 Contact

For questions, suggestions, or support, please open an issue on GitHub.

---

**Built with ❤️ using Next.js 16 and TypeScript**
