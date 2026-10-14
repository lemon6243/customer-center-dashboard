with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Bar chart fallback in HomePage
old_bar_block = '''        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=sorted_df['센터명'],
            y=sorted_df['총점'],
            marker=dict(color=bar_colors, line=dict(color='#0B4EA2', width=1)),
            text=[f"{v:.1f}" for v in sorted_df['총점']],
            textposition='auto',
            textfont=dict(size=10, weight=700)
        ))
        fig_bar.add_shape(
            type="line",
            x0=-0.5, x1=len(sorted_df)-0.5,
            y0=911, y1=911,
            line=dict(color="#EF4444", width=2, dash="dash")
        )
        min_s = max(0, sorted_df['총점'].min() - 30)
        max_s = min(1000, sorted_df['총점'].max() + 20)
        fig_bar.update_layout(
            height=360,
            margin=dict(l=10, r=10, t=25, b=60),
            xaxis_tickangle=-40,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(range=[min_s, max_s], gridcolor='#F1F5F9')
        )
        st.plotly_chart(fig_bar, use_container_width=True)'''

new_bar_block = '''        if HAS_PLOTLY:
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=sorted_df['센터명'],
                y=sorted_df['총점'],
                marker=dict(color=bar_colors, line=dict(color='#0B4EA2', width=1)),
                text=[f"{v:.1f}" for v in sorted_df['총점']],
                textposition='auto',
                textfont=dict(size=10, weight=700)
            ))
            fig_bar.add_shape(
                type="line",
                x0=-0.5, x1=len(sorted_df)-0.5,
                y0=911, y1=911,
                line=dict(color="#EF4444", width=2, dash="dash")
            )
            min_s = max(0, sorted_df['총점'].min() - 30)
            max_s = min(1000, sorted_df['총점'].max() + 20)
            fig_bar.update_layout(
                height=360,
                margin=dict(l=10, r=10, t=25, b=60),
                xaxis_tickangle=-40,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(range=[min_s, max_s], gridcolor='#F1F5F9')
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            bar_df = sorted_df.set_index('센터명')['총점']
            st.bar_chart(bar_df, height=360)'''

if old_bar_block in text:
    text = text.replace(old_bar_block, new_bar_block)
    print('Patched bar chart fallback!')

# 2. Trend chart fallback in CenterDetailPage
old_trend_block = '''    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend_df['평가연월'],
        y=trend_df['총점'],
        mode='lines+markers',
        name=f'{sel_center} 총점',
        line=dict(color='#0B4EA2', width=3),
        marker=dict(size=8)
    ))
    fig_trend.add_trace(go.Scatter(
        x=trend_df['평가연월'],
        y=[911.0]*len(trend_df),
        mode='lines',
        name='합격 기준(911점)',
        line=dict(color='#EF4444', width=2, dash='dash')
    ))
    fig_trend.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=20, b=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='#F1F5F9'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_trend, use_container_width=True)'''

new_trend_block = '''    if HAS_PLOTLY:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=trend_df['평가연월'],
            y=trend_df['총점'],
            mode='lines+markers',
            name=f'{sel_center} 총점',
            line=dict(color='#0B4EA2', width=3),
            marker=dict(size=8)
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend_df['평가연월'],
            y=[911.0]*len(trend_df),
            mode='lines',
            name='합격 기준(911점)',
            line=dict(color='#EF4444', width=2, dash='dash')
        ))
        fig_trend.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=20, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(gridcolor='#F1F5F9'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        trend_plot_df = trend_df.set_index('평가연월')[['총점']]
        st.line_chart(trend_plot_df, height=320)'''

if old_trend_block in text:
    text = text.replace(old_trend_block, new_trend_block)
    print('Patched trend chart fallback!')

# 3. Radar chart fallback in CenterDetailPage
old_radar_block = '''        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=radar_vals,
            theta=radar_cats,
            fill='toself',
            fillcolor='rgba(11, 78, 162, 0.25)',
            line=dict(color='#0B4EA2', width=2),
            name=sel_center
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor='#E2E8F0'),
                angularaxis=dict(tickfont=dict(size=10, color="#172B4D", weight=700))
            ),
            showlegend=False,
            height=320,
            margin=dict(l=25, r=25, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_radar, use_container_width=True)'''

new_radar_block = '''        if HAS_PLOTLY:
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=radar_vals,
                theta=radar_cats,
                fill='toself',
                fillcolor='rgba(11, 78, 162, 0.25)',
                line=dict(color='#0B4EA2', width=2),
                name=sel_center
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor='#E2E8F0'),
                    angularaxis=dict(tickfont=dict(size=10, color="#172B4D", weight=700))
                ),
                showlegend=False,
                height=320,
                margin=dict(l=25, r=25, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            radar_df = pd.DataFrame({'지표': radar_cats[:-1], '달성률(%)': [round(v, 1) for v in radar_vals[:-1]]})
            st.dataframe(radar_df, hide_index=True, use_container_width=True)'''

if old_radar_block in text:
    text = text.replace(old_radar_block, new_radar_block)
    print('Patched radar chart fallback!')

# 4. Heatmap fallback
old_heat_block = '''    fig_heat = px.imshow(
        heat_data,
        labels=dict(x="평가지표", y="고객센터", color="달성도"),
        x=kpi_names,
        y=heat_data.index,
        color_continuous_scale="Blues",
        aspect="auto"
    )
    fig_heat.update_layout(
        height=620,
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis_tickfont=dict(size=11, color="#1E293B", weight=700),
        yaxis_tickfont=dict(size=11, color="#1E293B")
    )
    st.plotly_chart(fig_heat, use_container_width=True)'''

new_heat_block = '''    if HAS_PLOTLY:
        fig_heat = px.imshow(
            heat_data,
            labels=dict(x="평가지표", y="고객센터", color="달성도"),
            x=kpi_names,
            y=heat_data.index,
            color_continuous_scale="Blues",
            aspect="auto"
        )
        fig_heat.update_layout(
            height=620,
            margin=dict(l=20, r=20, t=20, b=40),
            xaxis_tickfont=dict(size=11, color="#1E293B", weight=700),
            yaxis_tickfont=dict(size=11, color="#1E293B")
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.dataframe(heat_data.round(1), use_container_width=True)'''

if old_heat_block in text:
    text = text.replace(old_heat_block, new_heat_block)
    print('Patched heatmap fallback!')

# 5. Scatter and Corr fallbacks in DeepAnalysisPage
old_scatter_block = '''        fig_scatter = px.scatter(
            cur_df,
            x=x_col,
            y=y_col,
            text='센터명',
            trendline='ols' if len(cur_df) > 2 else None,
            labels={x_col: x_col, y_col: y_col}
        )
        fig_scatter.update_traces(
            textposition='top center',
            marker=dict(size=10, color='#0B4EA2', line=dict(width=1, color='white'))
        )
        fig_scatter.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=30, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(gridcolor='#F1F5F9'),
            xaxis=dict(gridcolor='#F1F5F9')
        )
        st.plotly_chart(fig_scatter, use_container_width=True)'''

new_scatter_block = '''        if HAS_PLOTLY:
            fig_scatter = px.scatter(
                cur_df,
                x=x_col,
                y=y_col,
                text='센터명',
                trendline='ols' if len(cur_df) > 2 else None,
                labels={x_col: x_col, y_col: y_col}
            )
            fig_scatter.update_traces(
                textposition='top center',
                marker=dict(size=10, color='#0B4EA2', line=dict(width=1, color='white'))
            )
            fig_scatter.update_layout(
                height=380,
                margin=dict(l=10, r=10, t=30, b=40),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(gridcolor='#F1F5F9'),
                xaxis=dict(gridcolor='#F1F5F9')
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.dataframe(cur_df[['센터명', x_col, y_col]], hide_index=True, use_container_width=True)'''

if old_scatter_block in text:
    text = text.replace(old_scatter_block, new_scatter_block)
    print('Patched scatter fallback!')

old_corr_block = '''        fig_corr = px.imshow(
            corr_mat,
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            text_auto=".2f"
        )
        fig_corr.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=30, b=40)
        )
        st.plotly_chart(fig_corr, use_container_width=True)'''

new_corr_block = '''        if HAS_PLOTLY:
            fig_corr = px.imshow(
                corr_mat,
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                text_auto=".2f"
            )
            fig_corr.update_layout(
                height=380,
                margin=dict(l=10, r=10, t=30, b=40)
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.dataframe(corr_mat.round(2), use_container_width=True)'''

if old_corr_block in text:
    text = text.replace(old_corr_block, new_corr_block)
    print('Patched corr fallback!')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('All Plotly fallbacks successfully integrated!')
