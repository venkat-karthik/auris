# 🎨 Auris Interactive Documentation Website

A beautiful, animated, and interactive HTML documentation website for the Auris Voice AI Platform with smooth transitions, visual workflows, and comprehensive guides.

## 📁 Files Structure

```
docs/
├── index.html           # Main documentation page
├── styles.css          # Complete styling with responsive design
├── animations.css      # 40+ animation definitions
├── script.js           # Interactive functionality
├── sections.html       # Additional sections (reference)
└── README.md          # This file
```

## 🚀 Features

### Visual Design
- **Modern Dark Theme**: Professional gradient backgrounds
- **Smooth Animations**: 40+ CSS animations for smooth transitions
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Interactive Elements**: Hover effects, transitions, and micro-interactions

### Navigation
- **Sticky Navbar**: Always-visible navigation with smooth scrolling
- **Active Link Tracking**: Automatically highlights current section
- **Mobile Menu**: Hamburger menu for smaller screens
- **Smooth Scroll**: Natural scrolling behavior throughout

### Workflows
- **5 Interactive Workflows**: Complete step-by-step demonstrations
- **Code Examples**: Real API calls with syntax highlighting
- **Visual Indicators**: Step numbers, status badges, arrows
- **Timeline View**: Timeline representation of workflow progress

### Sections Included
1. **Home/Hero**: Eye-catching introduction with key stats
2. **Overview**: Platform comparison and why choose Auris
3. **Architecture**: System diagram with pipeline visualization
4. **Workflows**: 5 detailed workflows with code examples
5. **Pricing**: Transparent pricing with cost comparisons
6. **APIs**: Quick API reference with 50+ endpoints
7. **Setup**: Step-by-step local development guide
8. **Footer**: Links and company information

## 🎬 Animations Included

### Fade Animations
- `fadeIn` - Basic fade effect
- `fadeInUp` - Fade while moving up
- `fadeInDown` - Fade while moving down
- `fadeInLeft` - Fade while moving left
- `fadeInRight` - Fade while moving right

### Slide Animations
- `slideInLeft` - Slide from left
- `slideInRight` - Slide from right
- `slideInUp` - Slide from bottom
- `slideInDown` - Slide from top

### Special Animations
- `float` - Continuous floating motion
- `pulse` - Pulsing scale effect
- `glow` - Glowing shadow effect
- `bounce` - Bouncing motion
- `rotate` - Rotation effect
- `arrowFlow` - Animated arrows
- `wave` - Wave motion (3 variations)
- `orbit` - Orbital motion
- `typewriter` - Typewriter text reveal
- `ripple` - Ripple effect on click
- `shimmer` - Shimmer loading effect

## 💻 How to Use

### 1. Open Locally
```bash
# Simply open the file in a web browser
open docs/index.html

# Or use a local server
cd docs
python -m http.server 8000
# Visit: http://localhost:8000
```

### 2. Navigate Sections
- Click navigation links to jump to sections
- Scroll naturally with smooth behavior
- Mobile hamburger menu for smaller screens

### 3. Interact with Workflows
- Click workflow tabs to switch between them
- Each workflow shows step-by-step progression
- Code examples are ready to copy (hover to reveal copy button)

### 4. View API Reference
- Browse 50+ endpoints by category
- Authentication, Agents, Calls, Knowledge Base, etc.
- Quick endpoint listings for reference

## 🎨 Customization

### Colors
Edit CSS variables in `styles.css`:
```css
:root {
    --primary-color: #9d4edd;
    --secondary-color: #00d9ff;
    --success-color: #06d6a0;
    --warning-color: #ffd60a;
    --danger-color: #ef476f;
    /* ... more variables */
}
```

### Fonts
Update font-family in `styles.css`:
```css
body {
    font-family: 'Your Custom Font', sans-serif;
}
```

### Animations
Modify animation durations and timing functions in `animations.css`:
```css
@keyframes fadeIn {
    /* Adjust animation timing here */
}
```

## 📱 Responsive Breakpoints

- **Desktop**: Full layout
- **Tablet (768px)**: Adjusted spacing, stacked content
- **Mobile (480px)**: Single column, simplified navigation

## ⚡ Performance Optimizations

- **CSS Grid & Flexbox**: Modern layout techniques
- **Hardware Acceleration**: GPU-accelerated animations
- **Lazy Loading**: Images load on scroll (optional)
- **Debounced Events**: Scroll event optimization
- **Minimal Dependencies**: No external libraries required

## 🔧 JavaScript Features

### Navigation
- Smooth scroll to sections
- Active link tracking
- Mobile hamburger menu

### Workflows
- Tab switching between 5 workflows
- Animation on workflow change
- Code block copy functionality

### Scroll Animations
- Intersection Observer for efficient animations
- Staggered animation delays
- Smooth fade-in effects

### Analytics (Optional)
- Track user interactions
- Monitor section views
- Performance metrics

## 📊 SEO Optimizations

- Semantic HTML structure
- Proper heading hierarchy
- Meta descriptions
- Open Graph tags
- Mobile-first design

## 🐛 Browser Support

- Chrome/Edge: Latest versions
- Firefox: Latest versions
- Safari: Latest versions
- Mobile browsers: iOS Safari, Chrome Mobile

## 📚 Content Sections

### Hero Section
- Eye-catching headline
- Key statistics (cost, latency, ownership)
- Call-to-action buttons
- Animated background circles

### Overview Section
- Why choose Auris
- Comparison cards (Retell, Vapi)
- Feature highlights

### Architecture Section
- System architecture diagram
- Pipeline visualization
- Processing latency breakdown
- Supporting services

### Workflows Section
- 5 interactive workflow tabs
- Step-by-step instructions
- Code examples for each step
- Timeline view

### Pricing Section
- 3 pricing tiers
- Cost per minute breakdown
- Real-world cost examples
- Competitive comparison table

### API Reference Section
- 6 API categories
- 50+ endpoints organized by type
- Quick endpoint listing

### Setup Section
- 4-step quick start guide
- Docker setup commands
- Python environment setup
- Server startup commands

## 🎯 Best Practices

1. **Use Consistent Colors**: Follow the CSS color variables
2. **Maintain Animation Timing**: Keep animation durations consistent
3. **Test Responsiveness**: Check on multiple devices
4. **Optimize Images**: Use appropriate image formats
5. **Accessibility**: Use semantic HTML and proper contrast

## 📝 Adding New Sections

1. Create new `<section>` with unique ID
2. Add to navigation menu
3. Apply animation classes to elements
4. Update styles as needed
5. Add JavaScript handlers if interactive

## 🚀 Deployment

### Static Hosting (Vercel, Netlify, GitHub Pages)
```bash
# Simply upload the docs folder
# No build process needed
```

### Docker Container
```dockerfile
FROM nginx:alpine
COPY docs /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose
```bash
docker build -t auris-docs .
docker run -p 80:80 auris-docs
```

## 📖 Documentation Files

This website complements:
- `WORKFLOW_DOCUMENTATION.md` - Detailed API reference
- `PRICING_AND_COSTS.md` - Complete pricing guide
- `QUICK_REFERENCE.md` - Command cheat sheet

## 🎓 Learning Resources

- **Beginner**: Start with Home and Overview sections
- **Developer**: Focus on Workflows and APIs
- **Finance**: Jump to Pricing section
- **DevOps**: Review Setup and Architecture

## 🤝 Contributing

To improve the documentation:
1. Update HTML content in `index.html`
2. Enhance styles in `styles.css`
3. Add animations to `animations.css`
4. Expand JavaScript in `script.js`

## 📄 License

MIT License - Same as Auris platform

## 📞 Support

- **GitHub**: https://github.com/venkat-karthik/auris
- **Email**: support@auris.xyz
- **Issues**: Report on GitHub

---

**Built for Auris Voice AI Platform**  
**Created by**: Venkat Karthik & Zovance  
**Last Updated**: July 21, 2026
